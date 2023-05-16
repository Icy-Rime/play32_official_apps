#!/bin/bash

mpypack build
cp -rf ".build/apps" "../play32_framework/.play32root"
micropython -X heapsize=4M "../play32_framework/boot.py"
