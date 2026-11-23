"""Independent geometry/alpha fixtures catch the previous centering and crop errors."""
import unittest
from PIL import Image
from slicing import sample_rect,register_frames

class SlicingTests(unittest.TestCase):
    def test_fractional_grid_keeps_consistent_cell_size(self):
        image=Image.new('RGBA',(1254,1254),(255,20,10,255))
        frames=[sample_rect(image,(i*1254/5,0,1254/5,1254/5)) for i in range(5)]
        self.assertEqual({im.size for im in frames},{(251,251)})
        self.assertEqual(frames[-1].info['sprite']['rect'][0]+frames[-1].info['sprite']['rect'][2],1254)

    def test_bottom_pivots_keep_feet_on_same_baseline(self):
        image=Image.new('RGBA',(40,60),(255,255,255,255))
        a=sample_rect(image,(0,0,20,20),pivot=(.5,0))
        b=sample_rect(image,(0,0,40,60),pivot=(.5,0))
        frames,geometry,origin=register_frames([a,b],'ThirdGroup')
        self.assertEqual(frames[0].size,frames[1].size)
        self.assertEqual(geometry[0]['offset'][1]+geometry[0]['renderSize'][1],origin[1])
        self.assertEqual(geometry[1]['offset'][1]+geometry[1]['renderSize'][1],origin[1])

    def test_yarn_body_reference_scale_is_applied(self):
        image=Image.new('RGBA',(100,100),(200,100,20,255))
        frame=sample_rect(image,(0,0,100,100),pivot=(.4,.2),scale=(2,3))
        _,geometry,_=register_frames([frame],'YarnObstacleV3')
        self.assertEqual(geometry[0]['renderSize'],[200,300])

    def test_game_material_rejects_low_alpha_matte(self):
        image=Image.new('RGBA',(3,1));image.putdata([(255,0,0,40),(255,0,0,102),(255,0,0,255)])
        frames,geometry,_=register_frames([sample_rect(image,(0,0,3,1))],'FiveBakedV80')
        x,y=geometry[0]['offset'];self.assertEqual([frames[0].getpixel((x+i,y))[3] for i in range(3)],[0,0,255])

    def test_outside_source_rect_is_rejected(self):
        with self.assertRaises(AssertionError):sample_rect(Image.new('RGBA',(10,10)),(9,0,2,2))

if __name__=='__main__':unittest.main()
