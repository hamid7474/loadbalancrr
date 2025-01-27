# متغیرها برای ذخیره اطلاعات
REMOTE_IP=""
LOCAL_IP=""
REMOTE_PASSWORD=""

# ساخت GRE Tunnel
create_gre_tunnel() {
    echo "Enter Local IPv4 or IPv6 Address:"
    read LOCAL_IP
    echo "Enter Remote IPv4 or IPv6 Address:"
    read REMOTE_IP

    # دستور ساخت GRE Tunnel
    sudo ip tunnel add gre1 mode gre local $LOCAL_IP remote $REMOTE_IP ttl 255
    sudo ip link set gre1 up
    sudo ip addr add 2001:470:1f10:e1f::1/64 dev gre1
    sudo ip -6 route add 2001:470:1f10:e1f::2 dev gre1

    # درخواست برای SSH دسترسی به سرور هدف
    echo "Enter SSH password for the Remote Server:"
    read REMOTE_PASSWORD

    # دستور SSH به سرور هدف برای پیکربندی GRE
    sshpass -p "$REMOTE_PASSWORD" ssh root@$REMOTE_IP <<EOF
    sudo ip tunnel add gre1 mode gre local $REMOTE_IP remote $LOCAL_IP ttl 255
    sudo ip link set gre1 up
    sudo ip addr add 2001:470:1f10:e1f::2/64 dev gre1
    sudo ip -6 route add 2001:470:1f10:e1f::1 dev gre1
    exit
EOF
}

# پاک کردن GRE Tunnel
delete_gre_tunnel() {
    # استفاده از آدرس ریموت و پسورد از قبل ذخیره شده
    echo "Deleting GRE Tunnel on Local and Remote Server..."
    sshpass -p "$REMOTE_PASSWORD" ssh root@$REMOTE_IP <<EOF
    sudo ip tunnel del gre1
    exit
EOF

    # پاک کردن GRE Tunnel در سرور لوکال
    sudo ip tunnel del gre1
}

# منو اصلی
main_menu() {
    while true; do
        echo "1. Create GRE Tunnel"
        echo "2. Delete GRE Tunnel"
        echo "3. Exit"
        read -p "Choose an option: " choice
        case $choice in
            1)
                create_gre_tunnel
                ;;
            2)
                delete_gre_tunnel
                ;;
            3)
                exit
                ;;
            *)
                echo "Invalid choice, please try again."
                ;;
        esac
    done
}

main_menu
