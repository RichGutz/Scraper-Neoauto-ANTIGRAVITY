cat << 'EOF' > /etc/systemd/system/restore-wol-cron.service
[Unit]
Description=Restaurar Cron de WOL en Inicio
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c '(crontab -l 2>/dev/null | grep -v "bridge_wol.sh"; echo "30 18 * * * /data/bridge_wol.sh >> /data/wol.log 2>&1"; echo "0 0 * * 1 /data/bridge_wol.sh >> /data/wol.log 2>&1") | crontab -'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable restore-wol-cron.service
systemctl start restore-wol-cron.service
crontab -l
