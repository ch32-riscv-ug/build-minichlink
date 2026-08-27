#!/usr/bin/env bash

# Release inputs maintained by this repository. Keep libusb updates deliberate:
# changing either value rebuilds the newest upstream commit with the next rN.
UPSTREAM_REPOSITORY="https://github.com/cnlohr/ch32fun.git"
UPSTREAM_DEFAULT_REF="master"
LIBUSB_VERSION="1.0.29"
LIBUSB_SHA256="5977fc950f8d1395ccea9bd48c06b3f808fd3c2c961b44b0c2e6e29fc3a70a85"
LIBUSB_URL="https://github.com/libusb/libusb/releases/download/v${LIBUSB_VERSION}/libusb-${LIBUSB_VERSION}.tar.bz2"
