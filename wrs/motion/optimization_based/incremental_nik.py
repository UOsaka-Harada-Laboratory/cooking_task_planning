import math
import numpy as np
import basis.robot_math as rm
import modeling.geometric_model as gm
import robot_sim.robots.ur3_dual.ur3_dual_take as ur3d


class IncrementalNIK(object):

    def __init__(self, robot_s, base):
        self.robot_s = robot_s
        self.base = base

    def gen_linear_motion(self,
                          component_name,
                          start_tcp_pos,
                          start_tcp_rotmat,
                          goal_tcp_pos,
                          goal_tcp_rotmat,
                          obstacle_list=[],
                          granularity=0.03,
                          seed_jnt_values=None,
                          toggle_debug=False,
                          toggle_sphere=False):
        """
        :param component_name:
        :param start_tcp_pos:
        :param start_tcp_rotmat:
        :param goal_tcp_pos:
        :param goal_tcp_rotmat:
        :param goal_info:
        :param obstacle_list:
        :param granularity:
        :return:
        author: weiwei
        date: 20210125
        """
        jnt_values_bk = self.robot_s.get_jnt_values(component_name)
        pos_list, rotmat_list = rm.interplate_pos_rotmat(start_pos=start_tcp_pos,
                                                         start_rotmat=start_tcp_rotmat,
                                                         goal_pos=goal_tcp_pos,
                                                         goal_rotmat=goal_tcp_rotmat,
                                                         granularity=granularity)
        jnt_values_list = []
        sphere_list = []
        robo_list = []
        if seed_jnt_values is None:
            seed_jnt_values = jnt_values_bk
        for (pos, rotmat) in zip(pos_list, rotmat_list):
            jnt_values = self.robot_s.ik(component_name, pos, rotmat, seed_jnt_values=seed_jnt_values)
            if jnt_values is None:
                print("IK not solvable in gen_linear_motion!")
                # if toggle_sphere:
                #     sphere_list.append(gm.gen_sphere(pos, rgba=[1, 0, 0, 1]))
                #     sphere_list[-1].attach_to(self.base)
                # #     for sphere in sphere_list:
                # #         sphere.detach()
                # #     for robo in robo_list:
                # #         robo.detach()
                # #     print('消えてますか？')
                #     self.base.run()
                #     for sphere in sphere_list:
                #         sphere.detach()
                self.robot_s.fk(component_name, jnt_values_bk)
                return None
            else:
                if toggle_sphere:
                    sphere_list.append(gm.gen_sphere(pos, rgba=[0, 1, 0, 1]))
                    sphere_list[-1].attach_to(self.base)
                    self.robot_s.fk(component_name, jnt_values)
                    robo_list.append(self.robot_s.gen_meshmodel())
                    robo_list[-1].attach_to(self.base)
                    self.base.run()
                self.robot_s.fk(component_name, jnt_values)
                cd_result, ct_points = self.robot_s.is_collided(obstacle_list, toggle_contact_points=True)
                # if cd_result:
                #     if toggle_debug:
                #         for ct_pnt in ct_points:
                #             gm.gen_sphere(ct_pnt).attach_to(base)
                #     print("Intermediate pose collided in gen_linear_motion!")
                #     self.robot_s.fk(component_name, jnt_values_bk)
                #     return None
                if cd_result:
                    print(f'{ct_points}で衝突しました')
                    if toggle_sphere:
                        for ct_pnt in ct_points:
                            sphere_list.append(gm.gen_sphere(pos, rgba=[0, 0, 1, 1], radius=0.01))
                            sphere_list[-1].attach_to(self.base)
                            self.base.run()
                        for robo in robo_list:
                            robo.detach()
                        for sphere in sphere_list:
                            sphere.detach()
                    # for ct_pnt in ct_points:
                    #     gm.gen_sphere(ct_pnt).attach_to(self.base)
                    self.robot_s.fk(component_name, jnt_values_bk)
                    return None
            jnt_values_list.append(jnt_values)
            seed_jnt_values = jnt_values
        for robo in robo_list:
            robo.detach()
        for sphere in sphere_list:
            sphere.detach()
        self.robot_s.fk(component_name, jnt_values_bk)
        return jnt_values_list

    def gen_rel_linear_motion(self,
                              component_name,
                              goal_tcp_pos,
                              goal_tcp_rotmat,
                              direction,
                              distance,
                              obstacle_list=[],
                              granularity=0.03,
                              seed_jnt_values=None,
                              type='sink',
                              toggle_debug=False,
                              toggle_sphere=False):
        """
        :param goal_info:
        :param direction:
        :param distance:
        :param obstacle_list:
        :param granularity:
        :param type: 'sink', or 'source'
        :return:
        author: weiwei
        date: 20210114
        """
        if type == 'sink':
            print(len(goal_tcp_pos))
            print(len(rm.unit_vector(direction)))
            print(rm.unit_vector(direction))
            print(distance)
            print(len(rm.unit_vector(direction) * distance))
            start_tcp_pos = goal_tcp_pos - rm.unit_vector(direction) * distance
            start_tcp_rotmat = goal_tcp_rotmat
            return self.gen_linear_motion(component_name,
                                          start_tcp_pos,
                                          start_tcp_rotmat,
                                          goal_tcp_pos,
                                          goal_tcp_rotmat,
                                          obstacle_list,
                                          granularity,
                                          seed_jnt_values,
                                          toggle_debug=toggle_debug,
                                          toggle_sphere=toggle_sphere)
        elif type == 'source':
            start_tcp_pos = goal_tcp_pos
            start_tcp_rotmat = goal_tcp_rotmat
            goal_tcp_pos = goal_tcp_pos + direction * distance
            goal_tcp_rotmat = goal_tcp_rotmat
            return self.gen_linear_motion(component_name,
                                          start_tcp_pos,
                                          start_tcp_rotmat,
                                          goal_tcp_pos,
                                          goal_tcp_rotmat,
                                          obstacle_list,
                                          granularity,
                                          seed_jnt_values,
                                          toggle_debug=toggle_debug,
                                          toggle_sphere=toggle_sphere)
        else:
            raise ValueError("Type must be sink or source!")

    def gen_rel_linear_motion_with_given_conf(self,
                                              component_name,
                                              goal_jnt_values,
                                              direction,
                                              distance,
                                              obstacle_list=[],
                                              granularity=0.03,
                                              seed_jnt_values=None,
                                              type='sink',
                                              toggle_debug=False):
        """
        :param goal_info:
        :param direction:
        :param distance:
        :param obstacle_list:
        :param granularity:
        :param type: 'sink', or 'source'
        :return:
        author: weiwei
        date: 20210114
        """
        goal_tcp_pos, goal_tcp_rotmat = self.robot_s.cvt_conf_to_tcp(component_name, goal_jnt_values)
        if type == 'sink':
            start_tcp_pos = goal_tcp_pos - rm.unit_vector(direction) * distance
            start_tcp_rotmat = goal_tcp_rotmat
            return self.gen_linear_motion(component_name,
                                          start_tcp_pos,
                                          start_tcp_rotmat,
                                          goal_tcp_pos,
                                          goal_tcp_rotmat,
                                          obstacle_list,
                                          granularity,
                                          seed_jnt_values,
                                          toggle_debug=toggle_debug)
        elif type == 'source':
            start_tcp_pos = goal_tcp_pos
            start_tcp_rotmat = goal_tcp_rotmat
            goal_tcp_pos = goal_tcp_pos + direction * distance
            goal_tcp_rotmat = goal_tcp_rotmat
            return self.gen_linear_motion(component_name,
                                          start_tcp_pos,
                                          start_tcp_rotmat,
                                          goal_tcp_pos,
                                          goal_tcp_rotmat,
                                          obstacle_list,
                                          granularity,
                                          seed_jnt_values,
                                          toggle_debug=toggle_debug)
        else:
            raise ValueError("Type must be sink or source!")

    def get_rotational_motion(self,
                              component_name,
                              start_tcp_pos,
                              start_tcp_rotmat,
                              goal_tcp_pos,
                              goal_tcp_rotmat,
                              obstacle_list=[],
                              rot_center=np.zeros(3),
                              rot_axis=np.array([1, 0, 0]),
                              granularity=0.03,
                              seed_jnt_values=None):
        # TODO
        pass

    def gen_circular_motion(self,
                            component_name,
                            circle_center_pos,
                            circle_ax,
                            start_tcp_rotmat,
                            end_tcp_rotmat,
                            radius=.02,
                            obstacle_list=[],
                            granularity=0.03,
                            seed_jnt_values=None,
                            toggle_tcp_list=False,
                            toggle_debug=False):
        """
        :param component_name:
        :param start_tcp_pos:
        :param start_tcp_rotmat:
        :param goal_tcp_pos:
        :param goal_tcp_rotmat:
        :param goal_info:
        :param obstacle_list:
        :param granularity:
        :return:
        author: weiwei
        date: 20210501
        """
        jnt_values_bk = self.robot_s.get_jnt_values(component_name)
        pos_list, rotmat_list = rm.interplate_pos_rotmat_around_circle(circle_center_pos,
                                                                       circle_ax,
                                                                       radius,
                                                                       start_tcp_rotmat,
                                                                       end_tcp_rotmat,
                                                                       granularity=granularity)
        # for (pos, rotmat) in zip(pos_list, rotmat_list):
        #     gm.gen_frame(pos, rotmat).attach_to(base)
        # base.run()
        jnt_values_list = []
        if seed_jnt_values is None:
            seed_jnt_values = jnt_values_bk
        for (pos, rotmat) in zip(pos_list, rotmat_list):
            jnt_values = self.robot_s.ik(component_name, pos, rotmat, seed_jnt_values=seed_jnt_values)
            if jnt_values is None:
                print("IK not solvable in gen_circular_motion!")
                self.robot_s.fk(component_name, jnt_values_bk)
                return []
            else:
                self.robot_s.fk(component_name, jnt_values)
                cd_result, ct_points = self.robot_s.is_collided(obstacle_list, toggle_contact_points=True)
                if cd_result:
                    if toggle_debug:
                        for ct_pnt in ct_points:
                            gm.gen_sphere(ct_pnt).attach_to(base)
                    print("Intermediate pose collided in gen_linear_motion!")
                    self.robot_s.fk(component_name, jnt_values_bk)
                    return []
            jnt_values_list.append(jnt_values)
            seed_jnt_values = jnt_values
        self.robot_s.fk(component_name, jnt_values_bk)
        if toggle_tcp_list:
            return jnt_values_list,[[pos_list[i], rotmat_list[i]] for i in range(len(pos_list))]
        else:
            return jnt_values_list


if __name__ == '__main__':
    import time
    import robot_sim.robots.yumi.yumi as ym
    import visualization.panda.world as wd
    import modeling.geometric_model as gm

    base = wd.World(cam_pos=[1.5, 0, 3], lookat_pos=[0, 0, .5])
    gm.gen_frame().attach_to(base)
    yumi_instance = ym.Yumi(enable_cc=True)
    component_name = 'rgt_arm'
    start_pos = np.array([.5, -.3, .3])
    start_rotmat = rm.rotmat_from_axangle([0, 1, 0], math.pi / 2)
    goal_pos = np.array([.55, .3, .5])
    goal_rotmat = rm.rotmat_from_axangle([0, 1, 0], math.pi / 2)
    gm.gen_frame(pos=start_pos, rotmat=start_rotmat).attach_to(base)
    gm.gen_frame(pos=goal_pos, rotmat=goal_rotmat).attach_to(base)
    inik = IncrementalNIK(yumi_instance)
    tic = time.time()
    jnt_values_list = inik.gen_linear_motion(component_name, start_tcp_pos=start_pos, start_tcp_rotmat=start_rotmat,
                                             goal_tcp_pos=goal_pos, goal_tcp_rotmat=goal_rotmat)
    toc = time.time()
    print(toc - tic)
    for jnt_values in jnt_values_list:
        yumi_instance.fk(component_name, jnt_values)
        yumi_meshmodel = yumi_instance.gen_meshmodel()
        yumi_meshmodel.attach_to(base)
    base.run()
