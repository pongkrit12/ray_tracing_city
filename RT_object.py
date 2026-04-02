# object class
import RT_utility as rtu
from RT_bvh import AABB
import RT_bvh as rtbvh
import math

class Object:
    def __init__(self) -> None:
        pass

    def intersect(self, rRay, cInterval):
        pass

    def aabb(self):
        pass

class Sphere(Object):
    def __init__(self, vCenter, fRadius, mMat=None) -> None:
        super().__init__()
        self.center = vCenter
        self.radius = fRadius
        self.material = mMat
        # additional parameters for motion blur
        self.moving_center = None       # where to the sphere moves to
        self.is_moving = False          # is it moving ?
        self.moving_dir = None          # moving direction

    def add_material(self, mMat):
        self.material = mMat

    def add_moving(self, vCenter):      # set an ability to move to the sphere
        self.moving_center = vCenter
        self.is_moving = True
        self.moving_dir = self.moving_center - self.center

    def move_sphere(self, fTime):       # move the sphere by time parameter
        return self.center + self.moving_dir*fTime

    def printInfo(self):
        self.center.printout()        
    
    def intersect(self, rRay, cInterval):        

        # check if the sphere is moving then move center of the sphere.
        sphere_center = self.center
        if self.is_moving:
            sphere_center = self.move_sphere(rRay.getTime())

        oc = rRay.getOrigin() - sphere_center
        a = rRay.getDirection().len_squared()
        half_b = rtu.Vec3.dot_product(oc, rRay.getDirection())
        c = oc.len_squared() - self.radius*self.radius
        discriminant = half_b*half_b - a*c 

        if discriminant < 0:
            return None
        sqrt_disc = math.sqrt(discriminant)

        root = (-half_b - sqrt_disc) / a 
        if not cInterval.surrounds(root):
            root = (-half_b + sqrt_disc) / a 
            if not cInterval.surrounds(root):
                return None
            
        hit_t = root
        hit_point = rRay.at(root)
        hit_normal = (hit_point - sphere_center) / self.radius
        hinfo = rtu.Hitinfo(hit_point, hit_normal, hit_t, self.material)
        hinfo.set_face_normal(rRay, hit_normal)

        # set uv coordinates for texture mapping
        fuv = self.get_uv(hit_normal)
        hinfo.set_uv(fuv[0], fuv[1])

        return hinfo

    # return uv coordinates of the sphere at the hit point.
    def get_uv(self, vNormal):
        theta = math.acos(-vNormal.y())
        phi = math.atan2(-vNormal.z(), vNormal.x()) + math.pi

        u = phi / (2*math.pi)
        v = theta / math.pi
        return (u,v)
    
    def aabb(self):
        min_pt = rtu.Vec3(self.center.x() - self.radius,
                           self.center.y() - self.radius,
                           self.center.z() - self.radius)
        max_pt = rtu.Vec3(self.center.x() + self.radius,
                           self.center.y() + self.radius,
                           self.center.z() + self.radius)
        return rtbvh.AABB(min_pt, max_pt)

# Ax + By + Cz = D
class Quad(Object):
    def __init__(self, vQ, vU, vV, mMat=None) -> None:
        super().__init__()
        self.Qpoint = vQ
        self.Uvec = vU
        self.Vvec = vV
        self.material = mMat
        self.uxv = rtu.Vec3.cross_product(self.Uvec, self.Vvec)
        self.normal = rtu.Vec3.unit_vector(self.uxv)
        self.D = rtu.Vec3.dot_product(self.normal, self.Qpoint)
        self.Wvec = self.uxv / rtu.Vec3.dot_product(self.uxv, self.uxv)

    def add_material(self, mMat):
        self.material = mMat

    def intersect(self, rRay, cInterval):
        denom = rtu.Vec3.dot_product(self.normal, rRay.getDirection())
        # if parallel
        if rtu.Interval.near_zero(denom):
            return None

        # if it is hit.
        t = (self.D - rtu.Vec3.dot_product(self.normal, rRay.getOrigin())) / denom
        if not cInterval.contains(t):
            return None
        
        hit_t = t
        hit_point = rRay.at(t)
        hit_normal = self.normal

        # determine if the intersection point lies on the quad's plane.
        planar_hit = hit_point - self.Qpoint
        alpha = rtu.Vec3.dot_product(self.Wvec, rtu.Vec3.cross_product(planar_hit, self.Vvec))
        beta = rtu.Vec3.dot_product(self.Wvec, rtu.Vec3.cross_product(self.Uvec, planar_hit))
        if self.is_interior(alpha, beta) is None:
            return None

        hinfo = rtu.Hitinfo(hit_point, hit_normal, hit_t, self.material)
        hinfo.set_face_normal(rRay, hit_normal)

        # set uv coordinates for texture mapping
        hinfo.set_uv(alpha, beta)

        return hinfo
    
    def is_interior(self, fa, fb):
        delta = 0   
        if (fa<delta) or (1.0<fa) or (fb<delta) or (1.0<fb):
            return None

        return True

    def aabb(self):
        # สมมติ Quad อยู่บน plane วางใน world axis-aligned
        verts = [
            self.Qpoint,
            self.Qpoint + self.Uvec,
            self.Qpoint + self.Vvec,
            self.Qpoint + self.Uvec + self.Vvec
        ]
        min_x = min(v.x for v in verts)
        min_y = min(v.y for v in verts)
        min_z = min(v.z for v in verts)
        max_x = max(v.x for v in verts)
        max_y = max(v.y for v in verts)
        max_z = max(v.z for v in verts)
        return rtbvh.AABB(rtu.Vec3(min_x, min_y, min_z),
                          rtu.Vec3(max_x, max_y, max_z))
    
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

    def intersect(self, rRay, cInterval):
        closest = cInterval.max_val
        hit_any = None

        for q in self.quads:
            hit = q.intersect(rRay, rtu.Interval(cInterval.min_val, closest))
            if hit:
                closest = hit.getT()
                hit_any = hit

        return hit_any
    
    def aabb(self):
        verts = []

        for quad in self.quads:
            verts.append(quad.Qpoint)
            verts.append(quad.Qpoint + quad.Uvec)
            verts.append(quad.Qpoint + quad.Vvec)
            verts.append(quad.Qpoint + quad.Uvec + quad.Vvec)

        min_x = min(v.x for v in verts)
        min_y = min(v.y for v in verts)
        min_z = min(v.z for v in verts)

        max_x = max(v.x for v in verts)
        max_y = max(v.y for v in verts)
        max_z = max(v.z for v in verts)

        return rtbvh.AABB(
            rtu.Vec3(min_x, min_y, min_z),
            rtu.Vec3(max_x, max_y, max_z)
        )


class Triangle(Object):
    def __init__(self) -> None:
        super().__init__()

    def intersect(self, rRay, cInterval):
        return super().intersect(rRay, cInterval)
    
    def aabb(self):
        return super().aabb()

    