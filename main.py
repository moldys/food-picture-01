"""food-picture-01 entry (Python 3.13, stdlib only): renders a food picture with
no external libraries — supersampled soft ray-march of a stack of pancakes with
syrup, butter, blueberries and strawberries on a plate, then writes PNG bytes
(hand-rolled PNG encoder using zlib/struct) to /output/entry.png. Deterministic.
"""
import struct, zlib, math, os

W, H = 1024, 1024
SS = 2          # supersample factor
IW, IH = W * SS, H * SS


def clamp(v, a=0.0, b=1.0):
    return a if v < a else b if v > b else v


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vlerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t)


# --- scene ---
def scene(x, y):
    """Return (color, depth) for pixel (x,y) in 0..1 space."""
    # background: warm restaurant wall gradient
    bg = vlerp((0.95, 0.82, 0.66), (0.55, 0.34, 0.22), y)
    # wooden table: bottom 42%
    if y > 0.58:
        plank = int((x * 5) % 1 * 8)
        t0 = 0.42 + 0.015 * math.sin(x * 90 + 1.3)
        bg = vlerp((0.42, 0.24, 0.13), (0.55, 0.33, 0.19), t0)
        gra = 0.5 + 0.5 * math.sin(x * 220 + y * 40)
        bg = vmul(bg, 0.9 + 0.1 * gra)
    # plate: broad white ellipse centered slightly above table
    px, py = 0.5, 0.52
    rx, ry = 0.40, 0.20
    dx = (x - px) / rx
    dy = (y - py) / ry
    d = dx * dx + dy * dy
    if d < 1.0:
        # plate shading
        rim = max(0.0, 1.0 - d)
        base = vlerp((0.98, 0.97, 0.94), (0.80, 0.78, 0.74), 1.0 - rim)
        shadow = 0.0
        if d < 0.85:
            shadow = 0.08
        bg = vmul(base, 1.0 - shadow)
    # food cluster centered at (0.5, 0.40)
    fx, fy = 0.5, 0.40
    # --- pancake stack: 4 ellipses stacked ---
    res = bg
    depth = 10.0
    for i, (ox, oy, rr, cc) in enumerate([
            (0.0, 0.0, 0.175, (0.93, 0.72, 0.38)),    # bottom
            (0.0, -0.055, 0.16, (0.90, 0.69, 0.36)),
            (0.0, -0.11, 0.145, (0.91, 0.70, 0.37)),
            (0.0, -0.165, 0.13, (0.89, 0.68, 0.35))]):  # top
        dx2 = (x - (fx + ox)) / rr
        dy2 = (y - (fy + oy)) / (rr * 0.42)

        if dx2 * dx2 + dy2 * dy2 < 1.0:
            # pancake surface: golden brown with darker edges
            dd = math.sqrt(dx2 * dx2 + dy2 * dy2)
            edge = clamp((dd - 0.75) / 0.25)
            col = vlerp((0.97, 0.78, 0.44), (0.72, 0.44, 0.20), edge)
            # speckle pores
            n = math.sin(x * 640 + y * 480 + i * 17.0)
            col = vmul(col, 0.97 + 0.03 * n)
            depth = min(depth, 4.0 + i * 0.3)
            res = col
    # --- syrup pooling on top pancake ---
    dx3 = (x - fx) / 0.10
    dy3 = (y - (fy - 0.165)) / 0.05
    if dx3 * dx3 + dy3 * dy3 < 1.0:
        syrup = (0.30, 0.16, 0.07)
        res = vlerp(res, syrup, 0.85)
        depth = min(depth, 2.0)
    # syrup drip streaks down the stack
    for k in range(3):
        sx = fx + (k - 1) * 0.09
        dx4 = (x - sx) / 0.035
        dy4 = (y - (fy - 0.03)) / 0.16
        if dx4 * dx4 + dy4 * dy4 < 1.0:
            res = vlerp(res, (0.32, 0.17, 0.07), 0.9)
            depth = min(depth, 3.0)
    # --- butter pat on top ---
    dx5 = (x - (fx + 0.03)) / 0.055
    dy5 = (y - (fy - 0.19)) / 0.04
    if dx5 * dx5 + dy5 * dy5 < 1.0:
        res = vlerp(res, (0.99, 0.96, 0.80), 0.95)
        depth = min(depth, 1.0)
    # --- blueberries ---
    for (bx, by) in [(0.17, -0.02), (0.22, 0.06), (0.12, 0.055)]:
        dx6 = (x - (fx + bx)) / 0.032
        dy6 = (y - (fy + by)) / 0.032
        if dx6 * dx6 + dy6 * dy6 < 1.0:
            bl = vlerp((0.18, 0.10, 0.36), (0.10, 0.05, 0.22),
                       math.sqrt(dx6 * dx6 + dy6 * dy6))
            hl = (x - (fx + bx) + 0.015) ** 2 + (y - (fy + by) + 0.015) ** 2
            bl = vlerp(bl, (0.55, 0.5, 0.75), clamp(1.0 - hl * 400.0))
            res = bl
            depth = min(depth, 0.8)
    # --- strawberries ---
    for (sx, sy) in [(0.20, -0.16), (0.24, -0.10)]:
        dx7 = (x - (fx + sx)) / 0.042
        dy7 = (y - (fy + sy)) / 0.042
        if dx7 * dx7 + dy7 * dy7 < 1.0:
            st = vlerp((0.80, 0.12, 0.10), (0.55, 0.06, 0.05),
                       math.sqrt(dx7 * dx7 + dy7 * dy7))
            seed = 0.5 + 0.5 * math.sin(x * 320.0 + y * 260.0)
            st = vlerp(st, (1.0, 0.85, 0.5), max(0.0, seed - 0.7))
            res = st
            depth = min(depth, 0.6)
    return res, depth


def render():
    """Supersampled render into RGB byte array."""
    px = bytearray(IW * IH * 3)
    for j in range(IH):
        y = 1.0 - (j + 0.5) / IH
        for i in range(IW):
            x = (i + 0.5) / IW
            col, _ = scene(x, y)
            off = (j * IW + i) * 3
            px[off] = int(clamp(col[0]) * 255)
            px[off + 1] = int(clamp(col[1]) * 255)
            px[off + 2] = int(clamp(col[2]) * 255)
    return px


def downsample(px):
    out = bytearray(W * H * 3)
    for j in range(H):
        for i in range(W):
            r = g = b = 0
            for dj in range(SS):
                for di in range(SS):
                    off = ((j * SS + dj) * IW + (i * SS + di)) * 3
                    r += px[off]
                    g += px[off + 1]
                    b += px[off + 2]
            n = SS * SS
            off = (j * W + i) * 3
            out[off] = r // n
            out[off + 1] = g // n
            out[off + 2] = b // n
    return out


def write_png(path, rgb, w, h):
    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I',
                               zlib.crc32(c) & 0xffffffff)
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter none
        s = y * stride
        raw += rgb[s:s + stride]
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)


def main():
    big = render()
    small = downsample(big)
    out = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out, exist_ok=True)
    write_png(os.path.join(out, 'entry.png'), small, W, H)


if __name__ == '__main__':
    main()
