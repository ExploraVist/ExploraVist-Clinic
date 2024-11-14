System Service Controls
restart service: sudo systemctl restart my_device.service

View Live Loges: sudo journalctl -u my_device.service -f

Enable and Start Service: sudo systemctl enable my_device.service

Check Service Status: sudo systemctl status my_device.service

Kill Service: sudo systemctl stop my_device.service
