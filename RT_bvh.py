# RT_bvh.py
import RT_utility as rtu

# ------------------------
# AABB class
# ------------------------
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
# ------------------------
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
# ------------------------
def traverse_bvh(ray, node, interval=None):
    if interval is None:
        interval = rtu.Interval(0.000001, rtu.infinity_number)
    if node is None or not node.box.hit(ray):
        return None
    if node.objects:  # leaf
        closest_hit = None
        for obj in node.objects:
            h = obj.intersect(ray, interval)
            if h and (closest_hit is None or h.t < closest_hit.t):
                closest_hit = h
        return closest_hit
    else:
        hit_left = traverse_bvh(ray, node.left, interval)
        hit_right = traverse_bvh(ray, node.right, interval)
        return closest_hit(hit_left, hit_right)

# ------------------------
# Helper functions
# ------------------------
def compute_bounding_box(objects):
    # combine object AABB to make node box
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

def closest_hit(hit1, hit2):
    # comparing two hits
    if hit1 is None:
        return hit2
    if hit2 is None:
        return hit1
    return hit1 if hit1.t < hit2.t else hit2