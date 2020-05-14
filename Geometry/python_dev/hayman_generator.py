import numpy.linalg
import numpy as np

import argparse, configparser

from math import pi, sqrt, cos, sin, acos, asin

# This script generates Mu2e hayman target descriptions for G4Beamline
# ... it's kind of yucky, but I want to keep it all in one file.

# This requires at least python 3.6, because I'm using fstrings

parser = argparse.ArgumentParser(description='Specify hayman parameter variations.')
parser.add_argument('configfile', help='INI configuration file')
parser.add_argument('outputfile', help='Generated G4Beamline file')
args = parser.parse_args()

config = configparser.ConfigParser()
config.read(args.configfile)

#################### Raw text

# TODO ... add comments about where the data comes from here
header_string = '''
### This is a generated file; do not edit!
###Regenerate with Geometry/python_dev/hayman_generator.py

# This file defines a representation of the Hayman style radiation
# cooled pion production target with four fins.
#
# The center point of the target is nominally located at
# (x, y, z) = (0.0, 0.0, 1764.5) (mm)
# The longitudinal axis of the target is rotated with respect to 
# the +y axis by 14 degrees
#
# This rotation is chosen to match the trajectory of the primary 
# proton beam through the axially graded PS field. 
#
# This target model allows for arbitrary rotations of the target
# around its center, followed by arbitrary translations away from its
# nominal position.
#
# - I always do the Y rotation, then the X rotation, then finally the
# Z rotation, before applying the offsets
#
# - The target rotations don't move the support ring or the outer
# ends of the support spokes.
#
# - The offsets also don't move the support ring (it's
# attached to the inside of the HRS), but do move the hub ends of the
# spokes.
# 
# - I assume the baseline HRS model (HRS-C) from the TDR; unfortunately,
# the current HRS-C implementation is entirely hardcoded rather than being
# parameterized, making it difficult to programatically extract the 

'''

enabletarget = config['Enable'].getint('Target')
enablewheel = config['Enable'].getint('BicycleWheel')
enablespokes = config['Enable'].getint('Spokes')

enable_string = f'''
param -unset EnableTarget={enabletarget}
param -unset EnableSpokes={enablespokes}
param -unset EnableBicycleWheel={enablewheel}
'''

# TODO: move to Mu2e.in/mu2e.in
params_string = f'''
material WL10 density=18.75 W,0.99 La,0.0085 O,0.0015
'''

BaseYangle = config['Target'].getfloat('BaseYangle')
# TODO: fix these .... should come from configuration parameters so
# the beam in mu2e.in can follow the target
params_string += f'''param TXangle=0
param TYangle={BaseYangle}
param TZangle=0
'''

######### strings for the target core and fins
core_radius = config['Target.Core'].getfloat('core_radius')
target_length = config['Target'].getfloat('target_length')
# TODO: ditto
params_string += f'param Tlength={target_length}'

Tmaterial = config['Target']['material']
core_long = f'tubs core_long outerRadius=%f length=%f material={Tmaterial} color=$Tungsten' % (core_radius, 5.)
core_short = f'tubs core_short outerRadius=%f length=%f material={Tmaterial} color=$Tungsten' % (core_radius, 2.5)
place_core_long = '\tplace core_long rename=+_core_%d z=%f\n'
place_core_short = '\tplace core_short rename=+_core_%d z=%f\n'
# TODO: more magic numbers ... put them in the configuration
core_length = [5] + [2.5]*12 + [5]*25
core_gap = [2]*23 + [1]*14 + [0] # last gap is filler to not blow up zip
offset = target_length/2.
target_bits_string = ''
for segment,(l,g) in enumerate(zip(core_length, core_gap)):
    if l == 5:
        target_bits_string += place_core_long%(segment, offset-l/2)
    elif l==2.5:
        target_bits_string += place_core_short%(segment, offset-l/2)
    else:
        print( 'Oops!', segment, l, g )
    offset -= l+g

end_ring_ir = config['Target.EndRings'].getfloat('ir')
end_ring_or = config['Target.EndRings'].getfloat('or')
end_ring_length = config['Target.EndRings'].getfloat('length')
end_ring_inset = config['Target.EndRings'].getfloat('inset')
end_ring_spoke = config['Target.EndRings'].getfloat('spoke')
end_ring = f'tubs end_ring innerRadius=%f outerRadius=%f length=%f material={Tmaterial} color=$Tungsten' % (end_ring_ir, end_ring_or, end_ring_length)
end_ring_location = (target_length+end_ring_length)/2-end_ring_inset
place_end_ring = '\tplace end_ring rename=+_%s z=%f\n'
target_bits_string += place_end_ring%('upstream', end_ring_location) 
target_bits_string += place_end_ring%('downstream', -end_ring_location)

total_gap_height = config['Target.Fins'].getfloat('total_gap_height')
fin_gap_height = total_gap_height-core_radius
total_height = config['Target.Fins'].getfloat('total_height')
fin_total_height = total_height-core_radius

chord_correction = (end_ring_ir - sqrt(64*end_ring_ir**2 - 16*1.)/8.)*2
fin_gap_height_clipped = end_ring_ir-chord_correction-core_radius

# TODO: more magic numbers
fin_long = f'box fin_long length=%f height=%f width=1. material={Tmaterial} color=$Tungsten' % (5., fin_gap_height-1e-3)
fin_long_clipped = f'box fin_long_clipped length=%f height=%f width=1. material={Tmaterial} color=$Tungsten' % (5., min(fin_gap_height,fin_gap_height_clipped)-1e-3)
fin_short = f'box fin_short length=%f height=%f width=1. material={Tmaterial} color=$Tungsten' % (2.5, fin_gap_height-1e-3)
fin_top = f'box fin_top length=%f height=%f width=1. material={Tmaterial} color=$Tungsten' % (target_length-end_ring_inset*2, fin_total_height-fin_gap_height)

place_fin_long = '\tplace fin_long rename=+_fin_%d_%d z=%f x=%f y=%f rotation=Z%d\n'
place_fin_long_clipped = '\tplace fin_long_clipped rename=+_fin_%d_%d z=%f x=%f y=%f rotation=Z%d\n'
place_fin_short = '\tplace fin_short rename=+_fin_%d_%d z=%f x=%f y=%f rotation=Z%d\n'
place_fin_top = '\tplace fin_top rename=+_fintop_%d z=0 x=%f y=%f rotation=Z%d\n'

# These may be rotating the wrong way relative to the offsets
angles = [0, 90., 180., 270.]
signx = [0,1,0,-1]
signy = [1,0,-1,0]
xoff = fin_gap_height/2+core_radius-0.5e-3
xoff_clipped = min(fin_gap_height, fin_gap_height_clipped)/2+core_radius-0.5e-3
offset = target_length/2
segments = len(core_length)
for segment,(l,g) in enumerate(zip(core_length, core_gap)):
    for fin,(a,sx,sy) in enumerate(zip(angles,signx,signy)):
        if l == 5:
            if segment==0 or segment==segments-1:
                target_bits_string += place_fin_long_clipped%(segment, fin, offset-l/2, sx*xoff_clipped, sy*xoff_clipped, a)
            else:
                target_bits_string += place_fin_long%(segment, fin, offset-l/2, sx*xoff, sy*xoff, a)
        elif l==2.5:
            target_bits_string += place_fin_short%(segment, fin, offset-l/2, sx*xoff, sy*xoff, a)
        else:
            print( 'Oops!', segment, l, g )
    offset -= l+g
xoff = (fin_total_height+fin_gap_height)/2+core_radius
for fin,(a,sx,sy) in enumerate(zip(angles,signx,signy)):
    target_bits_string += place_fin_top%(fin, sx*xoff, sy*xoff, a)

target_string = f'''
group pTarget material=Vacuum radius={max(end_ring_or, total_height)} length={target_length+2*end_ring_length-2*end_ring_inset}
{target_bits_string}
endgroup
'''

##### Now let's deal with the bicycle wheel....

TSupportRin = config['BicycleWheel'].getfloat('Rin')
TSupportRout = config['BicycleWheel'].getfloat('Rout')
TSupportRingThickness = config['BicycleWheel'].getfloat('RingThickness')
TSupportWheelMaterial = config['BicycleWheel']['WheelMaterial']
TSupportRingColor = config['BicycleWheel']['RingColor']
TSupportBumpRin = config['BicycleWheel'].getfloat('BumpRin')
TSupportBumpAngle = config['BicycleWheel'].getfloat('BumpAngle')

TSupportSpokeRodor = config['BicycleWheel.Rods'].getfloat('Rout')
TSupportSpokeRodLength = config['BicycleWheel.Rods'].getfloat('Length')
TSupportSpokeRodMaterial = config['BicycleWheel.Rods']['Material']
TSupportSpokeRodColor = config['BicycleWheel.Rods']['Color']

## Numpy calculation of rotation of points for support rod points
# points on wheel are rod center, us center, us bottom, ds center, ds bottom,
# points on hub are target us, target ds
# the extra 1mm offsets are for volume collision safety
wheelpoints = np.array([
    [0, 0, 0, 0, 0],
    [TSupportRin, TSupportRin, TSupportRin-TSupportSpokeRodor, TSupportRin, TSupportRin-TSupportSpokeRodor],
    [0, TSupportSpokeRodLength/2, TSupportSpokeRodLength/2, -TSupportSpokeRodLength/2, -TSupportSpokeRodLength/2]
])


huby = max(end_ring_or, total_height)
hubpoints = np.array([
    [0, 0],
    [huby, huby],
    [(target_length+end_ring_length-end_ring_inset-end_ring_spoke)/2, -(target_length+end_ring_length-end_ring_inset-end_ring_spoke)/2]
])

# rotation matrix generator functions assume angles in degrees!
def zrot(angle):
    phi = angle*pi/180
    return np.array([
        [cos(phi), -sin(phi), 0],
        [sin(phi), cos(phi), 0],
        [0, 0, 1]
    ])

def yrot(angle):
    phi = angle*pi/180
    return np.array([
        [cos(phi), 0, sin(phi)],
        [0, 1, 0],
        [-sin(phi), 0, cos(phi)]
    ])

def xrot(angle):
    phi = angle*pi/180
    return np.array([
        [1, 0, 0],
        [0, cos(phi), -sin(phi)],
        [0, sin(phi), cos(phi)]
    ])

# rotate primitive points to nominal positions
topzrot = -15
toprots = np.matmul(yrot(BaseYangle), zrot(topzrot))
toppoints = np.matmul(toprots, wheelpoints)
leftzrot = 120-15
leftrots = np.matmul(yrot(BaseYangle), zrot(leftzrot))
leftpoints = np.matmul(leftrots, wheelpoints)
rightzrot = -120-15
rightrots = np.matmul(yrot(BaseYangle), zrot(rightzrot))
rightpoints = np.matmul(rightrots, wheelpoints)

ring_wedges_string = f'''
tubs TSupportRingWedge_top innerRadius={TSupportRin} \\
   outerRadius={TSupportRout} length={TSupportRingThickness} \\
   initialPhi=30+0.001 finalPhi=150-0.001 \\
   material={TSupportWheelMaterial} color={TSupportRingColor}

tubs TSupportRingWedge_left innerRadius={TSupportRin} \\
   outerRadius={TSupportRout} length={TSupportRingThickness} \\
   initialPhi=150+0.001 finalPhi=270-0.001 \\
   material={TSupportWheelMaterial} color={TSupportRingColor}

tubs TSupportRingWedge_right innerRadius={TSupportRin} \\
   outerRadius={TSupportRout} length={TSupportRingThickness} \\
   initialPhi=-90+0.001 finalPhi=30-0.001 \\
   material={TSupportWheelMaterial} color={TSupportRingColor}

tubs TSupportBump innerRadius={TSupportBumpRin} \\
   outerRadius={TSupportRout} length={TSupportRingThickness} \\
   initialPhi={-TSupportBumpAngle/2} finalPhi={TSupportBumpAngle/2} \\
   material={TSupportWheelMaterial} color={TSupportRingColor}

tubs TSupportSpokeRod innerRadius=0 outerRadius={TSupportSpokeRodor} \\
   length={TSupportSpokeRodLength} \\
   material={TSupportSpokeRodMaterial} color={TSupportSpokeRodColor}

tubs TSupportSpokeRodDummy innerRadius=0 outerRadius={TSupportSpokeRodor+1e-3} \\
   length={TSupportSpokeRodLength} \\
   material={TSupportSpokeRodMaterial} color={TSupportSpokeRodColor}
'''
bumprotangle=270+7.5
ring_wedges_string += f'''
boolean op=union TSupportRingWedge_topa TSupportRingWedge_top TSupportBump z=0 \\
   x=0 y=0 rotation=Z{bumprotangle} \\
   material={TSupportWheelMaterial} color={TSupportRingColor}
boolean op=subtraction TSupportRing_topfinal TSupportRingWedge_topa TSupportSpokeRodDummy \\
   x={toppoints[0,0]} y={toppoints[1,0]} z={toppoints[2,0]} \\
   rotation=Y{-BaseYangle} \\
   material={TSupportWheelMaterial} color={TSupportRingColor}
'''
bumprotangle=150+7.49 # should be 7.5, but that crashes G4Beamline!
ring_wedges_string += f'''
boolean op=union TSupportRingWedge_lefta TSupportRingWedge_left TSupportBump z=0 \\
   x=0 y=0 rotation=Z{bumprotangle} \\
   material={TSupportWheelMaterial} color={TSupportRingColor}
boolean op=subtraction TSupportRing_leftfinal TSupportRingWedge_lefta TSupportSpokeRodDummy \\
   x={leftpoints[0,0]} y={leftpoints[1,0]} z={leftpoints[2,0]} \\
   rotation=Y{-BaseYangle} \\
   material={TSupportWheelMaterial} color={TSupportRingColor}
'''
bumprotangle=30+7.5
ring_wedges_string += f'''
boolean op=union TSupportRingWedge_righta TSupportRingWedge_right TSupportBump z=0 \\
   x=0 y=0 rotation=Z{bumprotangle} \\
   material={TSupportWheelMaterial} color={TSupportRingColor}
boolean op=subtraction TSupportRing_rightfinal TSupportRingWedge_righta TSupportSpokeRodDummy \\
   x={rightpoints[0,0]} y={rightpoints[1,0]} z={rightpoints[2,0]} \\
   rotation=Y{-BaseYangle} \\
   material={TSupportWheelMaterial} color={TSupportRingColor}
'''

##### all the attachment bits
# Support Ears for Robot to grab and the latches
TSupportEarHeight = config['BicycleWheel'].getfloat('EarHeight')
TSupportEarDepth = config['BicycleWheel'].getfloat('EarDepth')
TSupportEarThickness = config['BicycleWheel'].getfloat('EarThickness')
TSupportLatchRout = config['BicycleWheel'].getfloat('LatchRout')
TSupportLatchLength = config['BicycleWheel'].getfloat('LatchLength')
robot_bits_string = f'''
box TSupportEar length={TSupportEarDepth} width={TSupportEarThickness} \\
    height={TSupportEarHeight} \\
    material={TSupportWheelMaterial} color={TSupportRingColor}
tubs TSupportLatch innerRadius=0 outerRadius={TSupportLatchRout} \\
    length={TSupportLatchLength} material={TSupportWheelMaterial} \\
    color={TSupportRingColor}
'''
TSupportLatchZ = -TSupportRingThickness/2 - TSupportLatchLength/2 - 1e-3
TSupportEarZ = -TSupportEarDepth/2 - TSupportRingThickness/2 - 1e-3
TSupportEarX = TSupportRin + TSupportEarThickness/2
# TODO: more magic numbers
place_bicyclewheel_string = f'''
      place TSupportRing_topfinal z=0
      place TSupportRing_leftfinal z=0
      place TSupportRing_rightfinal z=0
      place TSupportSpokeRod rename=TSupportSpokeRod_top \\
      x={toppoints[0,0]} y={toppoints[1,0]} z={toppoints[2,0]} \\
      rotation=Y{BaseYangle} \\
      material={TSupportSpokeRodMaterial} color={TSupportSpokeRodColor}
      place TSupportSpokeRod rename=TSupportSpokeRod_left \\
      x={leftpoints[0,0]} y={leftpoints[1,0]} z={leftpoints[2,0]} \\
      rotation=Y{BaseYangle} \\
      material={TSupportSpokeRodMaterial} color={TSupportSpokeRodColor}
      place TSupportSpokeRod rename=TSupportSpokeRod_right \\
      x={rightpoints[0,0]} y={rightpoints[1,0]} z={rightpoints[2,0]} \\
      rotation=Y{BaseYangle} \\
      material={TSupportSpokeRodMaterial} color={TSupportSpokeRodColor}
      place TSupportLatch rename=TSupportLatch_top \\
         x=0 y={TSupportRin} z={TSupportLatchZ}
      place TSupportLatch rename=TSupportLatch_right \\
         x=cos(-30*degree)*{TSupportRin} \\
         y=sin(-30*degree)*{TSupportRin} \\
         z={TSupportLatchZ}
      place TSupportLatch rename=TSupportLatch_left \\
         x=cos(-150*degree)*{TSupportRin} \\
         y=sin(-150*degree)*{TSupportRin} \\
         z={TSupportLatchZ}
      place TSupportEar rename=+_Right \\
         z={TSupportEarZ} \\
         x={TSupportEarX} \\
         y=25.
       place TSupportEar rename=+_Left \\
         z={TSupportEarZ} \\
         x={-TSupportEarX} \\
         y=25.

'''

### finally, let's put in those spokes
TargetXoffset = config['Target'].getfloat('Xoff')
TargetYoffset = config['Target'].getfloat('Yoff')
TargetZoffset = config['Target'].getfloat('Zoff')
clockingAngle = config['Target'].getfloat('clockingAngle')
TYangle = BaseYangle + config['Target'].getfloat('Yrot')/1000.*180./pi
TXangle = config['Target'].getfloat('Xrot')/1000.*180./pi
TZangle = config['Target'].getfloat('Zrot')/1000.*180./pi

# rotate primitive points at end rings to final positions; again, we do Y->X->Z
mm = np.matmul
toprots = mm(zrot(TZangle), mm(xrot(TXangle), mm(yrot(TYangle), zrot(topzrot))))
leftrots = mm(zrot(TZangle), mm(xrot(TXangle), mm(yrot(TYangle), zrot(leftzrot))))
rightrots = mm(zrot(TZangle), mm(xrot(TXangle), mm(yrot(TYangle), zrot(rightzrot))))

Toffset = np.array([
    [TargetXoffset, TargetXoffset],
    [TargetYoffset, TargetYoffset],
    [TargetZoffset, TargetZoffset]
])

Ttoppoints = np.matmul(toprots, hubpoints)+Toffset
Tleftpoints = np.matmul(leftrots, hubpoints)+Toffset
Trightpoints = np.matmul(rightrots, hubpoints)+Toffset

Rpoints = [toppoints, leftpoints, rightpoints]
Tpoints = [Ttoppoints, Tleftpoints, Trightpoints]

TSpokeUpor = config['Spokes'].getfloat('SpokeUpor')
TSpokeDownor = config['Spokes'].getfloat('SpokeDownor')
spokes_string = ''
place_spokes_string = ''
# TODO: this could be cleaner
for i,(R,T) in enumerate(zip(Rpoints, Tpoints)):
    dvus = R.T[2]-T.T[0]
    center = (R.T[2]+T.T[0])/2
    rodspace = np.linalg.norm(dvus)
    rodlength = rodspace - 2*TSpokeUpor
    dvus2 = dvus.copy()
    dvus2[1] = 0
    rodspace_xz = np.linalg.norm(dvus2)
    fangle1 = asin(dvus[1]/rodspace)*180/pi
    fangle2 = asin(dvus[0]/rodspace_xz)*180/pi
    spokes_string += f'tubs rod{i}up innerRadius=0 outerRadius={TSpokeUpor} length={rodlength} material={Tmaterial} color=$Tungsten\n'
    place_spokes_string += f'place rod{i}up x={center[0]} y={center[1]} z={center[2]} rotation=X{fangle1},Y{-fangle2}\n'
    dvds = R.T[4]-T.T[1]
    center = (R.T[4]+T.T[1])/2
    rodspace = np.linalg.norm(dvds)
    rodlength = rodspace - 2*TSpokeDownor
    dvds2 = dvds.copy()
    dvds2[1] = 0
    rodspace_xz = np.linalg.norm(dvds2)
    fangle1 = asin(-dvds[1]/rodspace)*180/pi
    fangle2 = asin(-dvds[0]/rodspace_xz)*180/pi
    spokes_string += f'tubs rod{i}down innerRadius=0 outerRadius={TSpokeUpor} length={rodlength} material={Tmaterial} color=$Tungsten\n'
    place_spokes_string += f'place rod{i}down x={center[0]} y={center[1]} z={center[2]} rotation=X{fangle1},Y{-fangle2}\n'



 
##### now we place the target
place_ptarget = f'\tplace pTarget x={TargetXoffset} y={TargetYoffset} z={TargetZoffset} rotation=Z{clockingAngle},Y{TYangle},X{TXangle},Z{TZangle}'

#### the target group
# TODO: Magic number warning! This 200 should be $PSshield_r1
ptarget_group_header = f'group pTarget_group material=Vacuum radius={200-0.001} length={10.*25.4}\n'
ptarget_group_footer = f'endgroup\nplace pTarget_group x=0 y=0 z=$Tposition\n'

############ dump it all out here

with open(args.outputfile, 'w') as outfile:
    print(header_string, file=outfile)
    print(enable_string, file=outfile)
    print(params_string, file=outfile)
    if enabletarget:
        print(core_long, file=outfile)
        print(core_short, file=outfile)
        print(end_ring, file=outfile)
        print(fin_long, file=outfile)
        print(fin_long_clipped, file=outfile)
        print(fin_short, file=outfile)
        print(fin_top, file=outfile)
        print(target_string, file=outfile)
    if enablewheel:
        print(ring_wedges_string, file=outfile)
        print(robot_bits_string, file=outfile)
    if enablespokes:
        print(spokes_string, file=outfile)
    print(ptarget_group_header, file=outfile)
    if enabletarget:
        print(place_ptarget, file=outfile)
    if enablewheel:
        print(place_bicyclewheel_string, file=outfile)
    if enablespokes:
        print(place_spokes_string, file=outfile)
        pass
    print(ptarget_group_footer, file=outfile)
