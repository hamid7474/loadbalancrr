#!/bin/bash

# تابع برای نصب sshpass و haproxy
install_dependencies() {
    echo "Installing sshpass..."
    sudo apt-get install -y sshpass
    echo "Installing haproxy..."
    sudo apt-get install -y haproxy
}

# تابع برای گرفتن آدرس IP سرور هدف
get_target_ip() {
    echo "Enter target server IP (IPv4 or IPv6): "
    read target_ip
}

# تابع برای ساخت GRE Tunnel
create_gre_tunnel() {
    echo "Enter local IP: "
    read local_ip
    echo "Enter remote IP: "
    read remote_ip
    # ذخیره آدرس‌ها برای استفاده در پاک کردن GRE
    local saved_local_ip=$local_ip
    local saved_remote_ip=$remote_ip
    echo "Creating GRE Tunnel..."
    sudo ip tunnel add gre1 mode gre local $saved_local_ip remote $saved_remote_ip ttl 255
    sudo ip link set gre1 up
    sudo ip addr add 2001:470:1f10:e1f::1/64 dev gre1
    sudo ip -6 route add 2001:470:1f10:e1f::2 dev gre1
    # ذخیره آدرس ریموت برای استفاده در پاک کردن GRE
    echo $saved_remote_ip > /tmp/gre_remote_ip
    echo "GRE Tunnel created."
}

# تابع برای پاک کردن GRE Tunnel
delete_gre_tunnel() {
    if [ -f /tmp/gre_remote_ip ]; then
        remote_ip=$(cat /tmp/gre_remote_ip)
        echo "Deleting GRE Tunnel from remote server ($remote_ip)..."
        sshpass -p "$remote_password" ssh root@$remote_ip "sudo ip tunnel del gre1"
        echo "GRE Tunnel deleted."
        rm /tmp/gre_remote_ip
    else
        echo "GRE Tunnel not found!"
    fi
}

# منو
while true; do
    clear
    echo "===================="
    echo "Load Balancer Menu"
    echo "===================="
    echo "1. Set target server IP (IPv4 or IPv6)"
    echo "2. Set ports for load balancer"
    echo "3. Start Load Balancer"
    echo "4. Create GRE Tunnel"
    echo "5. Delete GRE Tunnel"
    echo "6. Remove Load Balancer"
    echo "7. Exit"
    echo "===================="
    echo -n "Choose an option: "
    read option
    case $option in
        1) 
            get_target_ip
            ;;
        2)
            # دریافت پورت‌ها برای لود بالانس
            ;;
        3)
            # استارت لود بالانس
            ;;
        4)
            create_gre_tunnel
            ;;
        5)
            delete_gre_tunnel
            ;;
        6)
            # حذف لود بالانس
            ;;
        7)
            exit 0
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
done

