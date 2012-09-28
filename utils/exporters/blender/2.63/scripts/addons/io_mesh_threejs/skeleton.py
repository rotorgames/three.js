import operator
import math
import mathutils

# ##############################################################################
# Model exporter - bones
# ##############################################################################

class BoneProxy:
    TEMPLATE_BONE = \
"""\
            {
                "parent" : %(parent)d,
                "name"   : "%(name)s",
                "pos"    : %(pos)s,
                "scl"    : %(scl)s,
                "rot"    : %(rot)s,
                "rotq"   : %(rotq)s
            }\
"""
    
    TEMPLATE_VEC3       = "[%g,%g,%g]"
    TEMPLATE_QUATERNION = "[%(x)g,%(y)g,%(z)g,%(w)g]"
    
    def __init__(self, bone, index=-1, prefix='', offset=None):
        
        if offset is None:
            offset = mathutils.Matrix.Identity(4)
        
        self._bone = bone
        
        self.offset = offset
        self.prefix = prefix
        self.parent_proxy = None
        self.index = index
                        
    #end: __init__
    
    def getBone(self):
        return self._bone
    
    def hasParent(self):
        return self._bone.parent is not None

    def getParentName(self):
        if self._bone.parent:
            return self._bone.parent.name
        return None

    def getBoneName(self):
        return self._bone.name
        
    def getProxyName(self):
        return self.prefix + self.getBoneName()
    
    def setParentProxy(self, parent_proxy=None):
    
        if self._bone.parent == parent_proxy._bone:
            self.parent_proxy = parent_proxy
            return True
            
        return False
    
    def getMatrix(self):
        if self.hasParent():
            return self._bone.matrix            
        else:
            return self.offset.to_3x3() * self._bone.matrix
    #end: getMatrix
    
    def getPosition(self, position = None):
        if position is None:
            position = mathutils.Vector( (0,0,0) )
        else:
            position = self._bone.matrix * position
            
        position += mathutils.Vector(self._bone.head)
        
        # now we're in the parent / armature local coordinates, but the origin is parent's tail
        
        parent = self._bone.parent
        if parent:
            # switch the origin to parent's head
            
            position += mathutils.Vector([0, parent.length, 0])
        else:
            # switch to global coordinates
            
            position = self.offset * position.to_4d()
            
        return position.to_3d()
    #end: getPosition
        
    def getQuaternion(self, quaternion = None):
    
        if quaternion is None:
        
            quaternion = mathutils.Quaternion()
            quaternion.identity()
        
        quaternion = self._bone.matrix.to_quaternion() * quaternion
        
        if not self.hasParent():
            
            quaternion = self.offset.to_quaternion() * quaternion
            
        return quaternion
    #end: getQuaternion
     
    def getEuler(self, euler = None):
        
        if euler is None:
                    
            matrix = mathutils.Matrix.Identity(3)
        else:
            matrix = euler.to_matrix()
            
        matrix = self._bone.matrix * matrix
        
        if not self.hasParent():
        
            matrix = self.offset.to_3x3() * matrix
    
        return 180.0 / math.pi * mathutils.Vector(matrix.to_euler())
    #end: getEuler
    
    def getScale(self, scale = None):
    
        if scale is None:
        
            return mathutils.Vector( (1,1,1) )
            
        return scale
    #end: getScale
        
    def getParentIndex(self):
    
        if self.parent_proxy:
            return self.parent_proxy.index
            
        return -1
    
    def render(self):
    
        pos  = self.getPosition()
        rot  = self.getEuler()
        scl  = self.getScale()
        rotq = self.getQuaternion()
          
        return self.TEMPLATE_BONE % {
            "parent" : self.getParentIndex(),
            "name"   : self.getProxyName(),
            "pos"    : self.TEMPLATE_VEC3 % (pos.x, pos.y, pos.z),
            "rot"    : self.TEMPLATE_VEC3 % (rot.x, rot.y, rot.z),
            "scl"    : self.TEMPLATE_VEC3 % (scl.x, scl.y, scl.z),
            "rotq"   : self.TEMPLATE_QUATERNION % {'w':rotq.w,'x':rotq.x,'y':rotq.y,'z':rotq.z},
        }
    #end: render
#end: class BoneProxy
    
class Skeleton:
    #TODO: switch all incoming armatures to 'REST' mode (?)
    
    def __init__(self, armature=None, name=None, layers=None, flipyz=False):        
        if armature:
            self.addArmature(armature, name, layers, flipyz)
        
        self.bones = {}        
    #end: __init__
    
    def addArmature(self, armature, name=None, offset=None, layers=None, flipyz=False):
        #TODO: only add bones from selected layer / layers (?)
        
        if armature is None:
            return False
        
        if offset is None:
            offset = mathutils.Matrix.Identity(4)
        
        if name is None:
            # in general this will be wrong :(
            name = armature.name      
        
        prefix = name + '.'
        for bone in armature.bones:
            unique_name = prefix + bone.name
            if unique_name in self.bones:
                print('Bone `%s` already in the skeleton - skipping.' % unique_name)
                continue
            
            self.bones[unique_name] = BoneProxy(bone,
                prefix = prefix,
                index  = len(self.bones),
                offset = offset,
            )
        
        for name, proxy in self.bones.items():
        
            if not proxy.hasParent():
                continue
                
            parent = self.bones.get(prefix + proxy.getParentName(), None)
            proxy.setParentProxy(parent)
            
        return True
    #end: addArmature
    
    def getBonesCount(self):
        return len(self.bones)
       
    def getBoneIndex(self, armature_name, bone_name):
    
        bone_name = armature_name + '.' + bone_name
        
        proxy = self.bones.get(bone_name, None)
        
        if proxy:
            return proxy.index
        return -1
        
    def iterBones(self):
        return sorted(self.bones.values(), key=operator.attrgetter('index'))
            
    def render(self):
        results = []
                
        for proxy in self.iterBones():
            results.append(proxy.render()) 
               
        return ",\n\n".join(results)
    #end: render
    
#end: class Skeleton
   

