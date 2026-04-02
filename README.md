# RT-python-final-project
new feature
# Russian Roulette
if maxDepth < 5:
    p = max(attenuation.r(), attenuation.g(), attenuation.b())
    p = min(max(p, 0.3),0.9)
    

    if random.random() > p:
        return rtu.Color(0,0,0)

    attenuation = attenuation / p

# ------------------------
# AABB class
class AABB:
    def __init__(self, min_pt, max_pt):
        self.min = min_pt  # rtu.Vec3
        self.max = max_pt

    # ray vs AABB intersection
    def hit(self, ray):
        tmin = (self.min.x - ray.origin.x) / ray.direction.x
        tmax = (self.max.x - ray.origin.x) / ray.direction.x
        if tmin > tmax: tmin, tmax = tmax, tmin

        tymin = (self.min.y - ray.origin.y) / ray.direction.y
        tymax = (self.max.y - ray.origin.y) / ray.direction.y
        if tymin > tymax: tymin, tymax = tymax, tymin

        if (tmin > tymax) or (tymin > tmax):
            return False
        tmin = max(tmin, tymin)
        tmax = min(tmax, tymax)

        tzmin = (self.min.z - ray.origin.z) / ray.direction.z
        tzmax = (self.max.z - ray.origin.z) / ray.direction.z
        if tzmin > tzmax: tzmin, tzmax = tzmax, tzmin

        if (tmin > tzmax) or (tzmin > tmax):
            return False
        return True

# ------------------------
# BVH Node class
class BVHNode:
    def __init__(self, objects):
        self.box = compute_bounding_box(objects)  # AABB

        if len(objects) <= 2:  # leaf node
            self.objects = objects
            self.left = None
            self.right = None
        else:
            # split along longest axis
            axis = box_longest_axis(self.box)
            objects.sort(key=lambda obj: obj.center.e[axis])
            mid = len(objects)//2
            self.left = BVHNode(objects[:mid])
            self.right = BVHNode(objects[mid:])
            self.objects = None

# ------------------------
# Traverse BVH
def traverse_bvh(ray, node):
    if node is None or not node.box.hit(ray):
        return None
    if node.objects:  # leaf
        hit = None
        for obj in node.objects:
            hit = closest_hit(hit, ray, obj)
        return hit
    else:
        hit_left = traverse_bvh(ray, node.left)
        hit_right = traverse_bvh(ray, node.right)
        return closest_hit(hit_left, hit_right)

# ------------------------
# Helper functions
def compute_bounding_box(objects):
    min_pt = rtu.Vec3(float('inf'), float('inf'), float('inf'))
    max_pt = rtu.Vec3(float('-inf'), float('-inf'), float('-inf'))
    for obj in objects:
        obj_box = obj.aabb()
        min_pt = rtu.Vec3(
        min(min_pt.x(), obj_box.min.x()),
        min(min_pt.y(), obj_box.min.y()),
        min(min_pt.z(), obj_box.min.z())
    )
    max_pt = rtu.Vec3(
        max(max_pt.x(), obj_box.max.x()),
        max(max_pt.y(), obj_box.max.y()),
        max(max_pt.z(), obj_box.max.z())
    )
    return AABB(min_pt, max_pt)

def box_longest_axis(box):
    dx = box.max.x() - box.min.x()
    dy = box.max.y() - box.min.y()
    dz = box.max.z() - box.min.z()
    if dx > dy and dx > dz:
        return 0  # x
    elif dy > dz:
        return 1  # y
    else:
        return 2  # z

def closest_hit(hit1, hit2, ray=None, obj=None):
    if obj is not None:
        h = obj.intersect(ray)
        if h is None:
            return hit1
        if hit1 is None or h.t < hit1.t:
            return h
        return hit1
    else:
        # comparing two hits
        if hit1 is None:
            return hit2
        if hit2 is None:
            return hit1
        return hit1 if hit1.t < hit2.t else hit2
# ------------------------
# render in tile
def render_tile(self, tile):
        x0, y0, x1, y1 = tile
        sqrt_spp = int(math.sqrt(self.camera.samples_per_pixel))
        tile_pixels = []

        for j in range(y0, y1):
            row = []
            for i in range(x0, x1):
                pixel_color = rtu.Color(0,0,0)
                for s_j in range(sqrt_spp):
                    for s_i in range(sqrt_spp):
                        ray = self.camera.get_jittered_ray(i, j, s_i, s_j)
                        pixel_color += self.integrator.compute_scattering(
                            ray, self.scene, self.camera.max_depth, self.integrator.use_fog
                        )
                row.append(pixel_color)

            tile_pixels.append(row)   # ✅ สำคัญมาก

        return (x0, y0, tile_pixels)
# ------------------------
# create tiles
    def create_tiles(self):
        tiles = []
        for y in range(0, self.camera.img_height, self.tile_size):
            for x in range(0, self.camera.img_width, self.tile_size):
                x1 = min(x + self.tile_size, self.camera.img_width)
                y1 = min(y + self.tile_size, self.camera.img_height)
                tiles.append((x, y, x1, y1))
        return tiles
# ------------------------
# parallel tile rendering
    def render_parallel_tiles(self):
        self.scene.find_lights()
        tiles = self.create_tiles()
        renderbar = RT_pbar.start_animated_marker(len(tiles))

        results = []
        with Pool(cpu_count()) as p:
            for k, result in enumerate(p.imap_unordered(self.render_tile, tiles)):
                results.append(result)
                renderbar.update(k + 1)

        renderbar.finish()

        # sort by row
        results.sort(key=lambda x: x[0])
        for x0, y0, tile in results:
            for dy, row in enumerate(tile):
                for dx, pixel_color in enumerate(row):
                    self.camera.write_to_film(x0 + dx, y0 + dy, pixel_color)

# ------------------------
# เพิ่มหมอกให้กับภาพ ต้องpresent ลืมพูดถึง มันจะเดิมสีเทาให้กับตึกที่อยู่ห่างออกไปสามารถเพิ่มความหนาของหมอกได้ด้วยการเพิ่มค่าdensity
if use_fog:
    distance = hinfo.getT()   # ใช้ระยะจริง (ดีกว่า direction)
    fog_color = rtu.Color(0.5, 0.5, 0.5)
    density = 0.08
    t = 1 - math.exp(-density * distance)
    color = color + (fog_color - color) * t
# ---------------------
# fog ถ้าไม่โดนobject
if use_fog:
            distance =10
            fog_color = rtu.Color(0.5, 0.5, 0.5)
            t = 1 - math.exp(-0.1 * distance)
            color = color + (fog_color - color) * t

        return color
# ---------------------
# class Box สำหรับทำตึก
class Box(Object):
    def __init__(self, center, width, height, depth, mat):
        super().__init__()

        self.quads = []
        self.material = mat

        x, y, z = center.x(), center.y(), center.z()
        w = width / 2
        d = depth / 2

        # --- define 8 vertices ---
        p0 = rtu.Vec3(x - w, 0, z - d)
        p1 = rtu.Vec3(x + w, 0, z - d)
        p2 = rtu.Vec3(x + w, 0, z + d)
        p3 = rtu.Vec3(x - w, 0, z + d)

        p4 = rtu.Vec3(x - w, height, z - d)
        p5 = rtu.Vec3(x + w, height, z - d)
        p6 = rtu.Vec3(x + w, height, z + d)
        p7 = rtu.Vec3(x - w, height, z + d)

        # --- create 6 faces using Quad ---
        self.quads.append(Quad(p0, p1 - p0, p4 - p0, mat))  # front
        self.quads.append(Quad(p2, p3 - p2, p6 - p2, mat))  # back
        self.quads.append(Quad(p3, p0 - p3, p7 - p3, mat))  # left
        self.quads.append(Quad(p1, p2 - p1, p5 - p1, mat))  # right
        self.quads.append(Quad(p4, p5 - p4, p7 - p4, mat))  # top
        self.quads.append(Quad(p0, p3 - p0, p1 - p0, mat))  # bottom