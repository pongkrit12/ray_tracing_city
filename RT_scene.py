# Scene class
import RT_utility as rtu
import numpy as np
import RT_object as rto
from RT_bvh import BVHNode, traverse_bvh 

class Scene:
    def __init__(self, cBgcolor=rtu.Color(0.01,0.01,0.01)) -> None:
        self.obj_list = []
        self.hit_list = None
        self.background_color = cBgcolor
        self.light_list = []
        self.point_light_list = []
        self.bvh_root = None
        pass

    def add_object(self, obj):
        self.obj_list.append(obj)

    def build_bvh(self):
        self.bvh_root = BVHNode(self.obj_list)

    def intersect(self, ray, interval=None):
        if interval is None:
            interval = rtu.Interval(0.000001, rtu.infinity_number)
        if self.bvh_root is not None:
            return traverse_bvh(ray, self.bvh_root, interval)
        else:
            # fallback loop ทุก object (แบบเดิม)
            closest_t = float('inf')
            hit_info = None
            for obj in self.obj_list:
                h = obj.intersect(ray, interval)
                if h is not None and h.getT() < closest_t:
                    closest_t = h.getT()
                    hit_info = h
            return hit_info

    def find_intersection(self, vRay, cInterval):
        self.hit_list = self.intersect(vRay, cInterval)
        return self.hit_list is not None

    # assume that if there is no occlusion, there is only 1 object is hit in the interval.
    # otherwise there will be an occlusion in the interval.
    def find_occlusion(self, vRay, cInterval):
        hit = self.intersect(vRay, cInterval)
        if hit and not hit.getMaterial().is_light():
            return True
        return False

    def getHitNormalAt(self, idx):
        return self.hit_list[idx].getNormal() 
    
    def getHitList(self):
        return self.hit_list

    def getBackgroundColor(self):
        return self.background_color

    def get_sky_background_color(self, rGen_ray):
        unit_direction = rtu.Vec3.unit_vector(rGen_ray.getDirection())
        a = (unit_direction.y() + 1.0)*0.5
        return rtu.Color(1,1,1)*(1.0-a) + rtu.Color(0.5, 0.7, 1.0)*a
    
    def find_lights(self):
        self.light_list = [] 
        self.point_light_list = []
        for obj in self.obj_list:
            if obj.material.is_light():
                self.light_list.append(obj)

        self.find_point_lights()

    def find_point_lights(self):
        for light in self.light_list:
            if isinstance(light, rto.Sphere):
                self.point_light_list.append(light)

