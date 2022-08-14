import network
import socket
import time
import gc
import neopixel

from machine import Pin

led = Pin(15, Pin.OUT)

ssid = 'YOUR_WIFI_NAME'
password = 'YOUR_WIFI_PASSWORD'
xres = 16
yres = 16
pin = 22
frameBytes = xres * yres * 2

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

wall = neopixel.NeoPixel(machine.Pin(pin), xres * yres)
wall.write()

def mapPixel(x, y):
    if y % 2 == 1:
        return xres * y + x
    else:
        return xres * y + xres - 1 - x

max_wait = 10
while max_wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    max_wait -= 1
    print('waiting for connection...')
    time.sleep(1)

if wlan.status() != 3:
    raise RuntimeError('network connection failed')
else:
    print('connected')
    status = wlan.ifconfig()
    print( 'ip = ' + status[0] )

addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]

s = socket.socket()
s.bind(addr)
s.listen(1)

print('listening on', addr)

# Listen for connections
while True:
    try:
        cl, addr = s.accept()
        # print('client connected from', addr)
        request = cl.recv(2048)
        # print(request)
        if len(request) >= 1:
            if request[0] == 80: # 'P' for post
                print("frame")
                for i in range(len(request) - 3):
                    if(request[i] == 13 and request[i + 1] == 10 and request[i + 2] == 13 and request[i + 3] == 10):
                        # found frame start
                        # print('found start at %d' % i)
                        start = i + 4;
                        while (len(request) - start < frameBytes):
                            request += cl.recv(2048)
                        # print('enough data %d' % (len(request) - start))
                        # print(request)
                        for y in range(yres):
                            for x in range(xres):
                                rgb = request[start] | (request[start + 1] << 8)
                                r = rgb & 31
                                g = (rgb >> 5) & 63
                                b = rgb >> 11
                                wall[mapPixel(x, y)] = (r<<2, g<<2, b<<2)
                                start += 2
                        wall.write()
						cl.send('HTTP/1.0 200 OK\r\nAccess-Control-Allow-Origin:*\r\n')
                        break
                            
            if request[0] == 71: # 'G' for GET
                print("serve")
                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\nhenlo')
        cl.close()
        #del request
        #del cl
        #del addr
        #gc.collect()

    except OSError as e:
        cl.close()
        print('connection closed')