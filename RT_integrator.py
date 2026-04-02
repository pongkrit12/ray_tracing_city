# a simple integrator class
# A ray is hit and then get the color.
# It is the rendering equation solver.
import RT_utility as rtu
import RT_ray as rtr
import RT_material as rtm
import math
import random

class Integrator():
    def __init__(self, bDlight=True, bSkyBG=False, use_fog=False) -> None:
        self.bool_direct_lighting = bDlight
        self.bool_sky_background = bSkyBG
        self.use_fog = use_fog
        pass

    def compute_scattering(self, rGen_ray, scene, maxDepth, use_fog=False):

        if maxDepth <= 0:
            return rtu.Color()
        
        # Russian Roulette
        #if maxDepth < 3:
        #    if random.random() < 0.3:
        #        return rtu.Color(0,0,0)
        
        # if the generated ray hits an object
        found_hit = scene.find_intersection(rGen_ray, rtu.Interval(0.000001, rtu.infinity_number))
        if found_hit == True:
            # get the hit info
            hinfo = scene.getHitList()
            # get the material of the object
            hmat = hinfo.getMaterial()
            # compute scattering
            sinfo = hmat.scattering(rGen_ray, hinfo)
            # if no scattering (It is a light source)
            if sinfo is None:
                # return Le
                return hmat.emitting()
            attenuation = sinfo.attenuation_color

            Le = rtu.Color()
            # if direct lighting is enabled
            if self.bool_direct_lighting:
                # for each point light
                for light in scene.point_light_list:
                    # check if there is an occlusion between a point light and a surface point.
                    tolight_dir = light.center - hinfo.getP()
                    distance = tolight_dir.len()
                    tolight_dir = rtu.Vec3.unit_vector(tolight_dir)
                    tolight_ray = rtr.Ray(hinfo.getP(), tolight_dir)
                    occlusion_hit = scene.find_occlusion(tolight_ray, rtu.Interval(0.000001, distance))
                    # if not occluded.
                    if not occlusion_hit:
                        # accumulate all unoccluded light
                        Le_BRDF = hmat.BRDF(rGen_ray, tolight_ray, hinfo)
                        # Le = Le + (Le_BRDF * light.material.emitting() * min(1.0, 1.0/max_distance))
                        NdotLe = rtu.Vec3.dot_product(hinfo.getNormal(), tolight_dir)
                        if NdotLe < 0:
                            NdotLe = 0.0
                        direct_L_i = light.material.emitting() / (distance * distance)
                        Le = Le + (Le_BRDF * direct_L_i * NdotLe)

            # return the color
            # Le*attennuation_color upto the point before reflection models otherwise it is not correct.
            NdotL = rtu.Vec3.dot_product(hinfo.getNormal(), sinfo.scattered_ray.getDirection())
            if NdotL < 1e-06:
                NdotL = 0.0

            if maxDepth < 5:
                p = max(attenuation.r(), attenuation.g(), attenuation.b())
                p = min(max(p, 0.3),0.9)
                

                if random.random() > p:
                    return rtu.Color(0,0,0)

                attenuation = attenuation / p

            L_i = self.compute_scattering(sinfo.scattered_ray, scene, maxDepth-1, self.use_fog)

            Fr =  hmat.BRDF(rGen_ray, sinfo.scattered_ray, hinfo)
            color = Le + (attenuation * L_i * NdotL)#Le + (attenuation * Fr * L_i * NdotL )

            # -------- FOG --------
            if use_fog:
                distance = hinfo.getT()   # ใช้ระยะจริง (ดีกว่า direction)
                fog_color = rtu.Color(0.5, 0.5, 0.5)
                density = 0.08
                t = 1 - math.exp(-density * distance)
                color = color + (fog_color - color) * t
            # ---------------------

            return color

        if self.bool_sky_background:
            color = scene.get_sky_background_color(rGen_ray)
        else:
            color = scene.getBackgroundColor()
        
        if use_fog:
            distance =10
            fog_color = rtu.Color(0.5, 0.5, 0.5)
            t = 1 - math.exp(-0.1 * distance)
            color = color + (fog_color - color) * t

        return color
