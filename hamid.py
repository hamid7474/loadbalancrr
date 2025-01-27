#!/bin/bash

# ذخیره‌سازی آدرس‌ها و پسوردها در متغیرها
local_ip=""
remote_ip=""
password=""

# منو اصلی
while true; do
    clear
    echo "------------------------"
    echo "1) Set Local and Remote IP"
    echo "2) Set Ports"
    echo "3) Start Load Balancer"
    echo "4) Create GRE Tunnel"
    echo "5) Delete GRE Tunnel"
    echo "6) Exit"
    echo "------------------------"
    read -p "Select an option: " option

    case $option in
        1) # تنظیم IP های Local و Remote
            echo "Enter Local IP:"
            read local_ip
            echo "Enter Remote IP:"
            read remote_ip
            # ذخیره پسورد برای ssh
            echo "Enter SSH password for the Remote server:"
            read -s password
            ;;
        2) # تنظیم پورت‌ها
            echo "Set Ports"
            ;;
        3) # استارت لود بالانس
            echo "Starting Load Balancer"
            ;;
        4) # ساخت GRE Tunnel
            if [[ -z "$local_ip" || -z "$remote_ip" ]]; then
                echo "Local IP and Remote IP must be set first!"
                read -p "Press any key to continue..."
                continue
            fi

            echo "Creating GRE Tunnel..."
            # اجرای دستورات GRE
            sudo ip tunnel add gre1 mode gre local $local_ip remote $remote_ip ttl 255
            sudo ip link set gre1 up
            sudo ip addr add 2001:470:1f10:e1f::1/64 dev gre1
            sudo ip -6 route add 2001:470:1f10:e1f::2 dev gre1

            # اتصال به سرور ریموت
            echo "Connecting to remote server..."
            sshpass -p "$password" ssh root@$remote_ip "sudo ip tunnel add gre1 mode gre local $remote_ip remote $local_ip ttl 255 && sudo ip link set gre1 up && sudo ip addr add 2001:470:1f10:e1f::2/64 dev gre1 && sudo ip -6 route add 2001:470:1f10:e1f::1 dev gre1"
            ;;
        5) # حذف GRE Tunnel
            if [[ -z "$local_ip" || -z "$remote_ip" ]]; then
                echo "Local IP and Remote IP must be set first!"
                read -p "Press any key to continue..."
                continue
            fi

            echo "Deleting GRE Tunnel..."
            sudo ip tunnel del gre1

            # حذف از سرور ریموت
            echo "Deleting GRE Tunnel on remote server..."
            sshpass -p "$password" ssh root@$remote_ip "sudo ip tunnel del gre1"
            ;;
        6) # خروج
            echo "Exiting..."
            break
            ;;
        *)
            echo "Invalid option!"
            ;;
    esac
done
