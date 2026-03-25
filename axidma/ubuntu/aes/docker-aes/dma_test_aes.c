#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <string.h>
#include <errno.h>

#define DMA_MAGIC 'D'
#define IOCTL_SELECT_CHANNEL     _IOW(DMA_MAGIC, 0, int)
#define IOCTL_DMA_WRITE_BUFFER   _IOW(DMA_MAGIC, 1, unsigned char *)
#define IOCTL_DMA_READ_BUFFER    _IOR(DMA_MAGIC, 2, unsigned char *)
#define IOCTL_DMA_START_TRANSFER _IOW(DMA_MAGIC, 3, size_t)
#define IOCTL_READ_STATUS_REGISTER     _IOR(DMA_MAGIC, 4, unsigned int*)
#define IOCTL_DMA_RESET _IOW(DMA_MAGIC, 5, size_t)
#define IOCTL_DMA_RESET_ALL _IOW(DMA_MAGIC, 6, size_t)

#define DEVICE_FILE "/dev/uniss_dma"
#define DMA_BUF_SIZE 65535

#define N_ITER 1000

void print_mem(void *virtual_address, int byte_count)
{
    char *data_ptr = virtual_address;

    for (int i = 0; i < byte_count; i++)
    {
        printf("%02X", (unsigned char)data_ptr[i]);

        // print a space every 4 bytes (0 indexed)
        if (i % 4 == 3)
        {
            printf(" ");
        }
    }

    printf("\n");
}

int main() {
    int fd = open(DEVICE_FILE, O_RDWR);
    if (fd < 0) {
        perror("Failed to open device");
        return 1;
    }

    // Prepare dummy data (allocazioni UNA sola volta)
    printf("Memory map the MM2S source address register blocks:\nTEXT\nKEY\nRC\n");
    unsigned int *virtual_src_TEXT_addr = (unsigned int*)malloc(DMA_BUF_SIZE);
    unsigned int *virtual_src_KEY_addr  = (unsigned int*)malloc(DMA_BUF_SIZE);

    printf("Memory map the S2MM destination address register block:\nENCRYPTED\n");
    unsigned int *virtual_dst_ENCRYPTED_addr = (unsigned int*)malloc(DMA_BUF_SIZE);

    unsigned int *buffer = (unsigned int*)malloc(sizeof(unsigned int));
    unsigned char *char_encr = (unsigned char*)malloc(DMA_BUF_SIZE);

    if (!virtual_src_TEXT_addr || !virtual_src_KEY_addr || !virtual_dst_ENCRYPTED_addr || !buffer || !char_encr) {
        perror("Failed to allocate buffers");
        free(virtual_src_TEXT_addr);
        free(virtual_src_KEY_addr);
        free(virtual_dst_ENCRYPTED_addr);
        free(buffer);
        free(char_encr);
        close(fd);
        return 1;
    }

    // Inizializza KEY una volta (se vuoi che resti sempre uguale)
    unsigned int j = 0x00000000;
    for (int i = 0; i < 32; ++i)
    {
        virtual_src_KEY_addr[i] = j;
        j = j + 0x1;
    }

    // LOOP 10k iterazioni
    for (int iter = 0; iter < N_ITER; ++iter) {

        int channel = 0;
        if (ioctl(fd, IOCTL_SELECT_CHANNEL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        printf("Writing text, key and rc data to userspace source buffers...\n");

        // text data FFEEDDCCBBAA99887766554433221100 (nel tuo esempio era una rampa 0x00,0x11,...)
        j = 0x00000000;
        for (int i = 0; i < 16; ++i)
        {
            virtual_src_TEXT_addr[i] = j;
            j = j + 0x11;
        }

        // 16 * 4 byte = 16 * 32 bit
        printf("Clearing the destination register block...\n");
        memset(virtual_dst_ENCRYPTED_addr, 0, 16 * 4);

        // print (se vuoi meno output, commenta queste stampe)
        printf("Text memory block data:      ");
        print_mem(virtual_src_TEXT_addr, 16 * 4);
        printf("Key memory block data:       ");
        print_mem(virtual_src_KEY_addr, 32 * 4);

        printf("Destination memory block data: ");
        print_mem(virtual_dst_ENCRYPTED_addr, 16 * 4);

        if (ioctl(fd, IOCTL_DMA_WRITE_BUFFER, virtual_src_TEXT_addr) < 0) {
            perror("Failed to write buffer to DMA");
            goto out;
        }

        printf("DMA buffer written successfully.\n");

        channel = 1;
        if (ioctl(fd, IOCTL_SELECT_CHANNEL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        if (ioctl(fd, IOCTL_DMA_WRITE_BUFFER, virtual_src_KEY_addr) < 0) {
            perror("Failed to write buffer to DMA");
            goto out;
        }

        printf("DMA buffer written successfully.\n");

        channel = 0;
        if (ioctl(fd, IOCTL_SELECT_CHANNEL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        if (ioctl(fd, IOCTL_DMA_RESET_ALL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        if (ioctl(fd, IOCTL_DMA_START_TRANSFER, 16) < 0) {
            perror("Failed to start DMA transfer");
            goto out;
        }

        printf("DMA transfer started.\n");

        channel = 1;
        if (ioctl(fd, IOCTL_SELECT_CHANNEL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        if (ioctl(fd, IOCTL_DMA_START_TRANSFER, 32) < 0) {
            perror("Failed to start DMA transfer");
            goto out;
        }

        printf("DMA transfer started.\n");

        channel = 2;
        if (ioctl(fd, IOCTL_SELECT_CHANNEL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        if (ioctl(fd, IOCTL_DMA_START_TRANSFER, 16) < 0) {
            perror("Failed to start DMA transfer");
            goto out;
        }

        printf("DMA transfer started.\n");

        channel = 0;
        if (ioctl(fd, IOCTL_SELECT_CHANNEL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        do{
            if (ioctl(fd, IOCTL_READ_STATUS_REGISTER, buffer) < 0) {
                perror("Failed to check status register");
                goto out;
            }
        } while(!(*buffer & (unsigned int)0x2));

        channel = 1;
        if (ioctl(fd, IOCTL_SELECT_CHANNEL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        do{
            if (ioctl(fd, IOCTL_READ_STATUS_REGISTER, buffer) < 0) {
                perror("Failed to check status register");
                goto out;
            }
        } while(!(*buffer & (unsigned int)0x2));

        channel = 2;
        if (ioctl(fd, IOCTL_SELECT_CHANNEL, channel) < 0) {
            perror("Failed to select DMA channel");
            goto out;
        }

        do{
            if (ioctl(fd, IOCTL_READ_STATUS_REGISTER, buffer) < 0) {
                perror("Failed to check status register");
                goto out;
            }
        } while(!(*buffer & (unsigned int)0x2));

        if (ioctl(fd, IOCTL_DMA_READ_BUFFER, char_encr) < 0) {
            perror("Failed to read buffer from DMA");
            goto out;
        }

        memcpy(virtual_dst_ENCRYPTED_addr, char_encr, 65535);

        // print (se vuoi solo fare 10k iterazioni senza flood, commenta)
        print_mem(char_encr, 16 * 4);
        print_mem(virtual_dst_ENCRYPTED_addr, 16 * 4);

        // (Opzionale) progress ogni N iterazioni; puoi commentare
        // if ((iter % 1000) == 0) fprintf(stderr, "iter %d/10000\n", iter);
    }

out:
    free(virtual_src_TEXT_addr);
    free(virtual_src_KEY_addr);
    free(virtual_dst_ENCRYPTED_addr);
    free(buffer);
    free(char_encr);
    close(fd);
    return 0;
}

