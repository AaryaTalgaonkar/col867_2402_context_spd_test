#!/bin/sh

echo "Turning Wi-Fi ON..."
nmcli radio wifi on
echo "Waiting for 20 seconds..."
sleep 20


echo "Running first_script.sh..."
go run main.go

echo "Turning Wi-Fi OFF..."
nmcli radio wifi off
echo "Waiting for 20 seconds..."
sleep 20


echo "Turning Wi-Fi ON again..."
nmcli radio wifi on

echo "Waiting for 20 seconds..."
sleep 20


echo "Running second_script.sh..."
go run main.go


echo "Turning Wi-Fi OFF..."
nmcli radio wifi off
echo "Waiting for 20 seconds..."
sleep 20


echo "Turning Wi-Fi ON again..."
nmcli radio wifi on

echo "Waiting for 20 seconds..."
sleep 20

echo "Running second_script.sh..."
go run main.go


echo "Turning Wi-Fi OFF..."
nmcli radio wifi off
echo "Waiting for 20 seconds..."
sleep 20


echo "Turning Wi-Fi ON again..."
nmcli radio wifi on

echo "Waiting for 20 seconds..."
sleep 20

echo "Running second_script.sh..."
go run main.go


echo "Turning Wi-Fi OFF..."
nmcli radio wifi off
echo "Waiting for 20 seconds..."
sleep 20


echo "Turning Wi-Fi ON again..."
nmcli radio wifi on

echo "Waiting for 20 seconds..."
sleep 20

echo "Running second_script.sh..."
go run main.go


echo "Turning Wi-Fi OFF..."
nmcli radio wifi off
echo "Waiting for 20 seconds..."
sleep 20


echo "Turning Wi-Fi ON again..."
nmcli radio wifi on

echo "Waiting for 20 seconds..."
sleep 20

echo "Running second_script.sh..."
go run main.go
