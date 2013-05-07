# -*- coding: utf-8 -*-
"""
@author: Lars, Olivier
"""
import time

import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

import numpy as np
import cv2

class Restore(object):
    
    def __init__(self, cm, dc, c2w_rmat, c2w_tvec, lplane, lpoint):
        self._cm = cm
        self._dc = dc
        self._w2c_rmat = c2w_rmat.T
        self._c2w_tvec = c2w_tvec
        self._lplane = lplane.reshape(3)
        self._lpoint = lpoint.reshape(3)

        self._l0 = np.dot(self._w2c_rmat, -self._c2w_tvec)
        self._l0 = self._l0.reshape(3)
        self._d1 = np.dot((self._lpoint - self._l0), self._lplane)

        #from IPython.frontend.terminal.embed import InteractiveShellEmbed
        #ipshell = InteractiveShellEmbed()
        #ipshell(local_ns=locals())

    
    def restore_old(self, line):
        ## resize array to get into correct shape for cv2.undistortPoints
        line = line.copy()
        nb = line.shape[0]
        line.resize(nb, 1, 2)

        ## undistort and normalize
        ud = cv2.undistortPoints(line, self._cm, self._dc)
        ud.shape = (nb, 2)
        ud_h = np.hstack((ud, np.ones((nb, 1))))
        
        # http://en.wikipedia.org/wiki/Line-plane_intersection        
        
        w2c_rmat = self._c2w_rmat.T
        p3d_array = []
        for udp in ud_h:
            pw = np.dot(w2c_rmat, udp.reshape(3,1) - self._c2w_tvec)
            l0 = np.dot(w2c_rmat, -self._c2w_tvec)
            l0 = l0.reshape(3)
            l = pw.reshape(3) - l0.reshape(3)
            ll = np.linalg.norm(l)
            if ll != 0:
                l /= ll
                
            n = self._lplane
            p0 = self._lpoint
            l = l.reshape(3)
            
            d1 = np.dot((p0 - l0), n)
            d2 = np.dot(l.reshape(3), n)
            
            p3d = (d1/d2)*l + l0 
            p3d_array.append(p3d)
            
            
        p3d_array = np.array(p3d_array)
        
        return p3d_array



    
    def undistort(self, line):
        ## resize array to get into correct shape for cv2.undistortPoints
        line = line.copy()
        nb = line.shape[0]
        line.resize(nb, 1, 2)

        ## undistort and normalize
        ud = cv2.undistortPoints(line, self._cm, self._dc)
        ud.shape = (nb, 2)
        ud = np.hstack((ud, np.ones((nb, 1))))
        return ud

    def transform(self, line):
        t1 = time.time()
        
        # http://en.wikipedia.org/wiki/Line-plane_intersection        
        
        p3d_array = []
        t2 = time.time()
        for udp in line:
            a1 = time.time()
            pw = np.dot(self._w2c_rmat, udp.reshape(3,1) - self._c2w_tvec)
            l0 = np.dot(self._w2c_rmat, - self._c2w_tvec)
            l0 = l0.reshape(3)
            l = pw.reshape(3) - l0.reshape(3)
            a2 = time.time()
            ll = np.linalg.norm(l)
            if ll != 0:
                l /= ll
                
            n = self._lplane
            p0 = self._lpoint
            l = l.reshape(3)
           
            a3 = time.time()
            d1 = np.dot((p0 - l0), n)
            d2 = np.dot(l.reshape(3), n)
            
            a4 = time.time()
            p3d = (d1/d2)*l + l0 
            p3d_array.append(p3d)
            
        print(": {}s,  {}s,  {}s".format(a2-a1, a3-a2, a4-a3))
        print("Expected inner loop time: ", (a4-a1) * 2048)
            
        p3d_array = np.array(p3d_array)
        t3 = time.time()
        print("init: {}s, loop {}s".format(t2-t1, t3-t2 ))
        
        return p3d_array


    def transform_op(self, line):
        p3d_array = []
        for udp in line:
            pw = np.dot(self._w2c_rmat, udp.reshape(3,1) - self._c2w_tvec)
            l = pw.reshape(3) - self._l0
            #print("l", l.shape, l)
            norm = np.linalg.norm(l)
            if norm != 0:
                l /= norm
            d2 = np.dot(l, self._lplane)
            p3d = (self._d1 / d2) * l + self._l0 
            p3d_array.append(p3d)
            
        p3d_array = np.array(p3d_array)
        return p3d_array


    def _v(self, udp):
        #print "UDP: ",  udp 
        #udp = np.array([x,y,z])
        pw = np.dot(self._w2c_rmat, udp.reshape(3,1) - self._c2w_tvec)
        l = pw.reshape(3) - self._l0
        norm = np.linalg.norm(l)
        if norm != 0:
            l /= norm
        d2 = np.dot(l, self._lplane)
        return (self._d1 / d2) * l + self._l0 

    def transform_op_v(self, line):
        #print line[0]
        return np.apply_along_axis(self._v, 1, line)
        #func = np.vectorize(self._v, excluded="udp")
        #return func(udp=line)




    def _format(self, line):
        nb = len(line)
        subpixel = 5
        line = line.copy()
        line = line.astype(np.float64)  / 2**subpixel
        line = line.reshape( nb, )
        x_range =  np.arange(0, nb, 1)
        line = np.vstack((x_range, line)).transpose()
        #print line
        #print line.shape
        return line

    def _format_op(self, line):
        nb = len(line)
        subpixel = 5
        #line = line.copy()
        line /= 2**subpixel
        line = line.reshape( nb, )
        x_range =  np.arange(0, nb, 1)
        line = np.vstack((x_range, line)).transpose()
        return line

    def restore(self, line):
        ## resize array to get into correct shape for cv2.undistortPoints
        t1 = time.time()
        line = self._format(line)
        t2 = time.time()
        line =  self.undistort(line)
        t3 = time.time()
        trans = self.transform(line)
        t4 = time.time()
        print("format: {}s, undistord {}s, transform {}s".format(t2-t1, t3-t2, t4-t3))
        return trans 

    def restore_op(self, line):
        ## resize array to get into correct shape for cv2.undistortPoints
        t1 = time.time()
        line = self._format(line)
        t2 = time.time()
        line =  self.undistort(line)
        t3 = time.time()
        trans = self.transform_op(line)
        t4 = time.time()
        print("format: {}s, undistord {}s, transform {}s".format(t2-t1, t3-t2, t4-t3))
        return trans 
      
        
    def plot3d(self, scan):
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        mpl.rcParams['legend.fontsize'] = 10
        for p3d in scan:
            xs, ys, zs = np.hsplit(p3d, 3)
            xs = xs.reshape(xs.shape[0])
            ys = ys.reshape(ys.shape[0])
            zs = zs.reshape(ys.shape[0])
            ax.plot(xs, ys, zs)
        plt.show()

       
    def plot3d_line(self, p3d1, p3d2=None):
        xs, ys, zs = np.hsplit(p3d1, 3)
        xs = xs.reshape(xs.shape[0])
        ys = ys.reshape(ys.shape[0])
        zs = zs.reshape(ys.shape[0])

        mpl.rcParams['legend.fontsize'] = 10

        fig = plt.figure()
        ax = fig.gca(projection='3d')
        ax.plot(xs, ys, zs, label='3d plot of laserline')
        if p3d2 is not None:
            xs2, ys2, zs2 = np.hsplit(p3d2, 3)
            xs2 = xs2.reshape(xs2.shape[0])
            ys2 = ys2.reshape(ys2.shape[0])
            zs2 = zs2.reshape(zs2.shape[0])
            ax.plot(xs2, ys2, zs2, label='3d plot of laserline #2')
            
        ax.legend()
        
        plt.show()


    #def show(self):
        #plt.show()
        
class Restore_op(Restore):            
    def __init__(self, *args):
        Restore.__init__(self, *args)
        self._c2w_tvec = self._c2w_tvec.reshape(3)

    def transform(self, line):
        p3dlist = []
        for udp in line:
            pw = np.dot(self._w2c_rmat, udp - self._c2w_tvec)
            #from IPython.frontend.terminal.embed import InteractiveShellEmbed
            #ipshell = InteractiveShellEmbed()
            #ipshell(local_ns=locals())
            l = pw - self._l0
            #print("l", l.shape, l)
            norm = np.linalg.norm(l)
            if norm != 0:
                l /= norm
            d2 = np.dot(l, self._lplane)
            p3d = (self._d1/d2) * l   + self._l0 
            p3dlist.append(p3d)
            
        p3d_array = np.array(p3dlist)
        return p3d_array


    def restore(self, line):
        ## resize array to get into correct shape for cv2.undistortPoints
        t1 = time.time()
        line = self._format_op(line)
        t2 = time.time()
        line =  self.undistort(line)
        t3 = time.time()
        trans = self.transform(line)
        t4 = time.time()
        print("format: {}s, undistord {}s, transform {}s".format(t2-t1, t3-t2, t4-t3))
        return trans 


  

            
        
        
        
    




if __name__ == '__main__':
    
    cm = np.load('../stepped_calibration_object/cm.npy')
    dc = np.load('../stepped_calibration_object/dc.npy')
    c2w_rmat = np.load('../stepped_calibration_object/c2w_rotmatrix.npy')
    c2w_tvec = np.load('../stepped_calibration_object/c2w_transvector.npy')
    ll2d = np.loadtxt('../stepped_calibration_object/laserline_2d.txt', dtype=np.float32)
    ll3d = np.loadtxt('../stepped_calibration_object/laserline_3d_in_object.txt', dtype=np.float32)
    lplane = np.loadtxt('../stepped_calibration_object/laser_plane.txt', dtype=np.float32)
    lpoint = np.loadtxt('../stepped_calibration_object/point_on_laser_plane.txt', dtype=np.float32)
    
    
    test_obj = LaserCalibrationSteppedObjectTest(cm, dc, c2w_rmat, c2w_tvec, ll2d, ll3d, lplane, lpoint)
    test_obj.plot3d(test_obj.intersect_with_laser_plane(), ll3d)
#    test_obj.plot3d(ll3d)
    test_obj.show()
    
    
    
    
