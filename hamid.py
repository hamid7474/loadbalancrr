#!/bin/bash

# ذخیره اطلاعات هدف و ریموت
target_ip=""
remote_ip=""

# نصب بسته های مورد نیاز
install_dependencies() {
    sudo apt-get install -y sshpass haproxy
}

# منوی اصلی
main_menu() {
    clear
    echo "===================================="
    echo "   Load Balancer & GRE Tunnel Setup"
    echo "===================================="
    echo "1. Set Target IP (IPv4 or IPv6)"
    echo "2. Set Ports"
    echo "3. Start Load Balancer"
    echo "4. Create GRE Tunnel"
    echo "5. Delete GRE Tunnel"
    echo "6. Delete Load Balancer"
    echo "7. Exit"
    read -p "Select an option: " choice
    case $choice in
        1) set_target_ip ;;
        2) set_ports ;;
        3) start_load_balancer ;;
        4) create_gre_tunnel ;;
        5) delete_gre_tunnel ;;
        6) delete_load_balancer ;;
        7) exit 0 ;;
        *) echo "Invalid option!" && sleep 2 && main_menu ;;
    esac
}

# تنظیم آدرس هدف (IPv4 یا IPv6)
set_target_ip() {
    read -p "Enter Target Server IP (IPv4 or IPv6): " target_ip
    main_menu
}

# تنظیم پورت‌ها
set_ports() {
    echo "Enter the ports to forward (comma separated, e.g., 80,443): "
    read ports
    # اینجا می‌تونید کدی اضافه کنید که پورت‌ها رو ذخیره یا مدیریت کنید
    main_menu
}

# شروع لود بالانسر
start_load_balancer() {
    # دستور برای شروع لود بالانسر
    echo "Starting Load Balancer..."
    sudo systemctl start haproxy
    main_menu
}

# ایجاد GRE Tunnel
create_gre_tunnel() {
    read -p "Enter Local IP for GRE: " local_ip
    read -p "Enter Remote IP for GRE: " remote_ip
    
    # ذخیره کردن آدرس‌های مربوطه برای استفاده بعدی
    echo "Creating GRE Tunnel..."
    sudo ip tunnel add gre1 mode gre local $local_ip remote $remote_ip ttl 255
    sudo ip link set gre1 up
    sudo ip addr add 2001:470:1f10:e1f::1/64 dev gre1
    sudo ip -6 route add 2001:470:1f10:e1f::2 dev gre1

    # اتصال به سرور ریموت برای تنظیم GRE آن
    echo "Connecting to remote server via SSH..."
    sshpass -p "$ssh_password" ssh root@$remote_ip << EOF
        sudo ip tunnel add gre1 mode gre local $remote_ip remote $local_ip ttl 255
        sudo ip link set gre1 up
        sudo ip addr add 2001:470:1f10:e1f::2/64 dev gre1
        sudo ip -6 route add 2001:470:1f10:e1f::1 dev gre1
EOF

    main_menu
}

# حذف GRE Tunnel
delete_gre_tunnel() {
    echo "Deleting GRE Tunnel from local server..."
    sudo ip tunnel del gre1
    echo "Deleting GRE Tunnel from remote server..."
    sshpass -p "$ssh_password" ssh root@$remote_ip << EOF
        sudo ip tunnel del gre1
EOF
    main_menu
}

# حذف لود بالانسر
delete_load_balancer() {
    echo "Removing Load Balancer (HAProxy)..."
    sudo apt-get remove --purge haproxy
    main_menu
}

# اجرای منو
main_menu
