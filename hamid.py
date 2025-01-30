#!/bin/bash

# متغیرها
ipv4=""
ipv6=""
target_server=""
remote_target_server="2001:470:1f10:e1f::2"  # آدرس ریموت برای GRE Tunnel
ports=()

# تابع نصب HAProxy اگر نصب نباشد
install_haproxy() {
    if ! command -v haproxy &> /dev/null; then
        echo "HAProxy not found. Installing..."
        sudo apt-get update
        sudo apt-get install -y haproxy sshpass
        echo "HAProxy installed successfully!"
    else
        echo "HAProxy is already installed."
    fi
}

# تابع نصب BBR
install_bbr() {
    echo "Installing BBR..."

    # فعال‌سازی BBR در کرنل
    sudo sysctl -w net.core.default_qdisc=fq
    sudo sysctl -w net.ipv4.tcp_congestion_control=bbr

    # ذخیره تنظیمات BBR
    echo "net.core.default_qdisc=fq" | sudo tee -a /etc/sysctl.conf
    echo "net.ipv4.tcp_congestion_control=bbr" | sudo tee -a /etc/sysctl.conf
    sudo sysctl -p

    # بررسی وضعیت BBR
    if sysctl net.ipv4.tcp_congestion_control | grep -q 'bbr'; then
        echo "BBR installed and activated successfully!"
    else
        echo "BBR installation failed."
    fi
}

# بررسی و نصب HAProxy در ابتدای اسکریپت
install_haproxy

# نصب و فعال‌سازی BBR
install_bbr

# تابع برای بررسی وضعیت نصب HAProxy
check_haproxy_status() {
    if command -v haproxy &> /dev/null; then
        echo "HAProxy Status: Installed"
    else
        echo "HAProxy Status: Not Installed"
    fi
}

# تابع برای گرفتن آدرس IP سرور محلی
get_local_ip() {
    local_ipv4=$(hostname -I | awk '{print $1}')
    local_ipv6=$(ip -6 addr show scope global | grep inet6 | awk '{print $2}' | cut -d/ -f1 | head -n 1)

    echo "Server IPv4: $local_ipv4"
    echo "Server IPv6: $local_ipv6"
}

# تابع برای گرفتن آدرس هدف (IPv4 یا IPv6)
set_target_ip() {
    echo "Which IP version do you want to enter for the target server?"
    echo "1) IPv4"
    echo "2) IPv6"
    echo -n "Choose an option: "
    read ip_choice

    if [[ $ip_choice -eq 1 ]]; then
        echo -n "Enter Target IPv4 Address: "
        read target_server
        ipv4=$target_server
        ipv6=""
    elif [[ $ip_choice -eq 2 ]]; then
        echo -n "Enter Target IPv6 Address: "
        read target_server
        ipv6=$target_server
        ipv4=""
    else
        echo "Invalid choice. Please try again."
        set_target_ip
    fi

    echo "Target server set to: $target_server"
}

# تابع برای تنظیم پورت‌ها
set_ports() {
    ports=()
    echo "Enter ports to forward (comma-separated, e.g., 80,443,8080): "
    read port_input

    # جدا کردن پورت‌ها و اضافه کردن به آرایه
    IFS=',' read -r -a ports <<< "$port_input"

    echo "Ports set: ${ports[*]}"
}

# تابع برای شروع Load Balancer
start_load_balancer() {
    if [[ -z "$target_server" || ${#ports[@]} -eq 0 ]]; then
        echo "Target server and ports must be set before starting the Load Balancer!"
        return
    fi

    # ساخت فایل کانفیگ HAProxy
    sudo bash -c 'cat > /etc/haproxy/haproxy.cfg' <<EOF
global
    log /dev/log    local0
    log /dev/log    local1 notice
    daemon

defaults
    log     global
    option  tcplog
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms

frontend http_front
EOF

   # اضافه کردن frontend و backend برای هر پورت
    for port in "${ports[@]}"; do
        sudo bash -c "echo '' >> /etc/haproxy/haproxy.cfg"
        sudo bash -c "echo 'frontend front_$port' >> /etc/haproxy/haproxy.cfg"
        sudo bash -c "echo '    bind *:$port' >> /etc/haproxy/haproxy.cfg"
        sudo bash -c "echo '    default_backend back_$port' >> /etc/haproxy/haproxy.cfg"
        sudo bash -c "echo '' >> /etc/haproxy/haproxy.cfg"
        
        sudo bash -c "echo 'backend back_$port' >> /etc/haproxy/haproxy.cfg"
        sudo bash -c "echo '    server target_$port $target_server:$port check' >> /etc/haproxy/haproxy.cfg"
    done

    # ری‌استارت HAProxy
    sudo systemctl restart haproxy
    echo "Load Balancer started successfully!"
}
# تابع برای ایجاد GRE Tunnel
create_gre_tunnel() {
    echo -n "Enter Iran IPv4 Address: "
    read local_ip
    echo -n "Enter Kharej IPv4 Address: "
    read remote_ip

    echo "Setting up GRE Tunnel..."

    # اجرای دستورات GRE Tunnel روی سرور محلی
    sudo ip tunnel add gre1 mode gre local $local_ip remote $remote_ip ttl 255
    sudo ip link set gre1 up
    sudo ip addr add 2001:470:1f10:e1f::1/64 dev gre1
    sudo ip -6 route add 2001:470:1f10:e1f::2 dev gre1

    # اتصال به سرور ریموت via SSH و اجرای دستورات
    echo -n "Enter Remote SSH IP Address: "
    read remote_ssh_ip
    echo -n "Enter SSH Password: "
    read -s ssh_password

    # اجرای دستورات GRE Tunnel روی سرور ریموت
    sshpass -p "$ssh_password" ssh -o StrictHostKeyChecking=no root@$remote_ssh_ip << EOF
        sudo ip tunnel add gre1 mode gre local $remote_ip remote $local_ip ttl 255
        sudo ip link set gre1 up
        sudo ip addr add 2001:470:1f10:e1f::2/64 dev gre1
        sudo ip -6 route add 2001:470:1f10:e1f::1 dev gre1
        exit
EOF

    echo "GRE Tunnel setup completed on remote server."

    # آدرس هدف ریموت را به متغیر target_server اضافه می‌کنیم
    target_server=$remote_target_server
}

# تابع برای حذف GRE Tunnel
remove_gre_tunnel() {
    echo -n "Enter Remote SSH IP Address: "
    read remote_ssh_ip
    echo -n "Enter SSH Password: "
    read -s ssh_password

    echo "Removing GRE Tunnel on local server..."
    sudo ip tunnel del gre1

    echo "Removing GRE Tunnel on remote server..."
    sshpass -p "$ssh_password" ssh -o StrictHostKeyChecking=no root@$remote_ssh_ip << EOF
        sudo ip tunnel del gre1
        exit
EOF

    echo "GRE Tunnel removed successfully from both local and remote servers."
}

# تابع برای حذف کامل HAProxy
remove_haproxy() {
    sudo systemctl stop haproxy
    sudo apt-get purge -y haproxy
    echo "HAProxy removed successfully!"
}

# تابع برای پاک کردن کانفیگ Load Balancer
clear_load_balancer_config() {
    sudo systemctl stop haproxy
    sudo rm /etc/haproxy/haproxy.cfg
    echo "Load Balancer config cleared."
}

# منو اصلی
while true; do
    clear
    echo "========= Server Info ========="
    get_local_ip
    echo "Target Server: ${target_server:-Not Set}"
    echo "$(check_haproxy_status)"
    echo "==============================="
    echo "1) Set Target Server IP (IPv4/IPv6)"
    echo "2) Set Ports"
    echo "3) Start Load Balancer"
    echo "4) Create GRE Tunnel"
    echo "5) Remove GRE Tunnel"
    echo "6) Remove Load Balancer"
    echo "7) Clear Load Balancer Config"
    echo "8) Exit"
    echo "==============================="
    echo -n "Choose an option: "
    read option

    case $option in
        1)
            set_target_ip
            ;;
        2)
            set_ports
            ;;
        3)
            start_load_balancer
            ;;
        4)
            create_gre_tunnel
            ;;
        5)
            remove_gre_tunnel
            ;;
        6)
            remove_haproxy
            ;;
        7)
            clear_load_balancer_config
            ;;
        8)
            echo "Exiting..."
            break
            ;;
        *)
            echo "Invalid option. Please try again."
            ;;
    esac
    read -p "Press [Enter] to continue..."
done
