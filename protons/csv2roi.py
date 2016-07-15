import os,sys
from ROOT import larcv as larcv

class image_def:
    def __init__(self):
        """ cols: 864 rows: 756 3456.0 0.0 8448.0 2400.0 """
        self._rows = 756
        self._cols = 864
        self._max_x = 3456.0
        self._min_x = 0.0
        self._max_y = 8448.0
        self._min_y = 2400.0

    def cols(self):
        return self._cols
    def rows(self):
        return self._rows
    def max_x(self):
        return self._max_x
    def max_y(self):
        return self._max_y
    def min_x(self):
        return self._min_x
    def min_y(self):
        return self._min_y

def roi2imgcord(imm,size,pos,img_coordinates=True):
    """ stolen from Vic """
    x = pos[0]
    y = pos[1]
    
    if not img_coordinates:
        # in pixel coordinates
        dw_i = imm.cols() / (imm.max_x() - imm.min_x())
        dh_i = imm.rows() / (imm.max_y() - imm.min_y())
    else:
        dw_i = 1.0
        dh_i = 1.0
    
    x /= dw_i
    y /= dh_i
    
        # the origin
    #origin_x = x + imm.min_x()
    #origin_y = y + imm.min_y()
    origin_x = x
    origin_y = y
    
    # w_b is width of a rectangle in original unit
    w_b = size[0]
    h_b = size[1]
    
    # the width
    width  = w_b / dw_i
    height = h_b / dh_i
    
    # for now...
    row_count = 0
    col_count = 0

    # vic isn't sure why this is needed
    origin_y += height

    return (width,height,row_count,col_count,origin_x,origin_y)

# we make dictionary of ROIs from Erez's file
ferez = open("selected_GBDTcandidates_score_95.csv",'r')
lerez = ferez.readlines()

img = image_def()

roi_dict = {}
for l in lerez[1:]:
    info = l.strip().split(",")
    run = int(info[0].strip())
    subrun = int(info[1].strip())
    event = int(info[2].strip())
    x1 = float(info[4].strip())
    y1 = float(info[5].strip())
    x2 = float(info[6].strip())
    y2 = float(info[7].strip())

    rse = (run,subrun,event)
    if rse not in roi_dict:
        roi_dict[rse] = larcv.EventROI()

    # make ROIs: U,V,Y = R,G,B in viewer


    # Uplane
    dt = y2-y1
    dw = x2-x1
    print dw,dt

    upos  = (0,y1+dt)
    usize = (dw,dt)
    # Vplane
    vpos  = (35,y1+dt)
    vsize = (dw,dt)
    # Uplane
    ypos  = (x1,y1+dt)
    ysize = (dw,dt)

    roi = larcv.ROI()
    print "Filling: ",rse
    for plane, (pos,size) in enumerate( [ (upos,usize), (vpos,vsize), (ypos,ysize) ] ):
        #width,height,row_count,col_count,origin_x,origin_y = roi2imgcord( img, size, pos, img_coordinates=True )
        #bbox_meta = larcv.ImageMeta(width,height,row_count,col_count,origin_x,origin_y,plane)
        bbox_meta = larcv.ImageMeta(size[0],size[1],0,0,pos[0],pos[1],plane)
        roi.AppendBB(bbox_meta)
    
    roi_dict[rse].Append(roi)


print "Number of entries: ",len(roi_dict)


# Now, open proton file and an output file.

input  = larcv.IOManager(larcv.IOManager.kREAD)
output = larcv.IOManager(larcv.IOManager.kWRITE)

input.add_in_file( "larcv_merged.root" )
input.initialize()

output.set_out_file( "output_proton_roi.root" )
output.initialize()

for entry in xrange( input.get_n_entries() ):
#for entry in xrange( 10 ): # for debug
    input.read_entry( entry )

    in_imgs = input.get_data( larcv.kProductImage2D, "tpc" )
    in_rse = (in_imgs.run(),in_imgs.subrun(),in_imgs.event())

    out_event_roi = output.get_data( larcv.kProductROI, "protonBDT" )
    output.set_id( in_rse[0], in_rse[1], in_rse[2] )

    if in_rse in roi_dict:
        print "Transfer ROIs for event (%d of %d): "%(entry,input.get_n_entries()),in_rse
        eventroi = roi_dict[in_rse]
        for roi in eventroi.ROIArray():
            out_event_roi.Append( roi )
    else:
        raise ValueError("Missing Event: %s"%(in_rse))

    output.save_entry()

output.finalize()


    

