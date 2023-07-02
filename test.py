import torch
import torch.nn.functional as F
import sys
sys.path.append('./models')
import numpy as np
import os, argparse
import cv2
from models.TR17 import SwinTransformer,SwinNet
from data import test_dataset

parser = argparse.ArgumentParser()
parser.add_argument('--testsize', type=int, default=384, help='testing size')
parser.add_argument('--gpu_id', type=str, default='0', help='select gpu id')
parser.add_argument('--test_path',type=str,default='/mnt/harddisk1/Yangfeng/codespace/dataset/testdata/',help='test dataset path')
opt = parser.parse_args()

dataset_path = opt.test_path

#set device for test
if opt.gpu_id=='0':
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    print('USE GPU 0')
elif opt.gpu_id=='1':
    os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    print('USE GPU 1')

#load the model
model = SwinNet()
model.load_state_dict(torch.load('./cpts/CMW-EGNet_epoch_best.pth'))
model.cuda()
model.eval()


# test

test_datasets = ['DUT','SIP','SSD','NJU2K','NLPR','STERE','RGBD135','LFSD']


for dataset in test_datasets:
    save_path = './test_maps/' + dataset + '/'
    edge_save_path = './test_maps/' + dataset + '/edge/'

    if not os.path.exists(save_path):
        os.makedirs(save_path)
    if not os.path.exists(edge_save_path):
        os.makedirs(edge_save_path)

    image_root = dataset_path + dataset + '/RGB/'
    gt_root = dataset_path + dataset + '/GT/'
    depth_root = dataset_path + dataset + '/depth/'
    test_loader = test_dataset(image_root, gt_root, depth_root, opt.testsize)
    for i in range(test_loader.size):
        image, gt, depth, name, image_for_post = test_loader.load_data()
        gt = np.asarray(gt, np.float32)
        gt /= (gt.max() + 1e-8)
        image = image.cuda()
        depth = depth = depth.repeat(1,3,1,1).cuda()
        res, edge, map3, map2, map1 = model(image,depth)
        res = F.upsample(res, size=gt.shape, mode='bilinear', align_corners=False)
        edge = F.upsample(edge, size=gt.shape, mode='bilinear', align_corners=False)
        res = res.sigmoid().data.cpu().numpy().squeeze()
        edge = edge.sigmoid().data.cpu().numpy().squeeze()
        res = (res - res.min()) / (res.max() - res.min() + 1e-8)
        edge = (edge - edge.min()) / (edge.max() - edge.min() + 1e-8)
        print('save img to: ',save_path+name)
        cv2.imwrite(save_path + name, res*255)
        cv2.imwrite(edge_save_path + name, edge * 255)
    print('Test Done!')
