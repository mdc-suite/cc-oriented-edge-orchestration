FROM mfois13/yocto-distro:latest

COPY . /resnet50

# Copiamo il file di configurazione corretto per vart.conf
COPY ./config/vart.conf /etc/vart.conf

# Impostiamo la directory di lavoro
WORKDIR /resnet50/

# Comando di avvio
CMD ["sh", "-c", "cp -r benchmark-b4096 /lib/firmware/xilinx && xmutil unloadapp && xmutil loadapp benchmark-b4096 && python3 app_mt.py"]
