FROM mcr.microsoft.com/vscode/devcontainers/base:bullseye

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Configure apt and install packages
RUN apt-get update  
RUN apt-get install -y gnupg software-properties-common 

RUN mkdir -m755 -p /etc/apt/keyrings
RUN wget -O /etc/apt/keyrings/qgis-archive-keyring.gpg https://download.qgis.org/downloads/qgis-archive-keyring.gpg

RUN apt-get update 
RUN apt-get install -y qgis qgis-plugin-grass

# copy src to container
COPY ./src .