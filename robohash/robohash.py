# This Python file uses the following encoding: utf-8
import os
import hashlib
from PIL import Image
import natsort
import random
import pprint as pp

class Robohash(object):
    """
    Robohash is a quick way of generating unique avatars for a site.
    The original use-case was to create somewhat memorable images to represent a RSA key.
    """

    def __init__(self, string, hashcount=11,ignoreext = True):
        """
        Creates our Robohasher
        Takes in the string to make a Robohash out of.
        """

        # Optionally remove an images extension before hashing.
        if ignoreext is True:
            string = self._remove_exts(string)

        mom, dad = string.split(":")
        mom = mom.encode('utf-8')
        dad = dad.encode('utf-8')

        self.momhex = hashlib.sha512(mom).hexdigest()
        self.dadhex = hashlib.sha512(dad).hexdigest()

        self.hasharray, self.parts_from = self._create_hashes(hashcount)
        self.momhasharray = self._create_hashes(hashcount, self.momhex)
        self.dadhasharray = self._create_hashes(hashcount, self.dadhex)

        #Start this at 4, so earlier is reserved
        #0 = Color
        #1 = Set
        #2 = bgset
        #3 = BG
        self.iter = 4

        self.resourcedir = os.path.dirname(__file__) + '/'
        # Get the list of backgrounds and RobotSets
        self.sets = self._listdirs(self.resourcedir + 'sets')
        self.bgsets = self._listdirs(self.resourcedir + 'backgrounds')

        # Get the colors in set1
        self.colors = self._listdirs(self.resourcedir + 'sets/set1')
        self.format = 'png'

    def _remove_exts(self,string):
        """
        Sets the string, to create the Robohash
        """

        # If the user hasn't disabled it, we will detect image extensions, such as .png, .jpg, etc.
        # We'll remove them from the string before hashing.
        # This ensures that /Bear.png and /Bear.bmp will send back the same image, in different formats.

        if string.lower().endswith(('.png','.gif','.jpg','.bmp','.jpeg','.ppm','.datauri')):
            format = string[string.rfind('.') +1 :len(string)]
            if format.lower() == 'jpg':
                format = 'jpeg'
            self.format = format
            string = string[0:string.rfind('.')]
        return string


    def _create_hashes(self, count, hex=None):
        """
        Breaks up our hash into slots, so we can pull them out later.
        Essentially, it splits our SHA/MD5/etc into X parts.
        """
        hasharray = []
        parts_from = []
        for i in range(0,count):
            #Get 1/numblocks of the hash
            blocksize = int(len(self.momhex) / count)
            currentstart = (1 + i) * blocksize - blocksize
            currentend = (1 +i) * blocksize
            if hex is None:
                if(random.random() > 0.5):
                    hasharray.append(int(self.momhex[currentstart:currentend],16))
                    parts_from.append("m")
                else:
                    hasharray.append(int(self.dadhex[currentstart:currentend],16))
                    parts_from.append("d")
            else:
                hasharray.append(int(hex[currentstart:currentend], 16))
        return hasharray, parts_from

    def _listdirs(self,path):
        return [d for d in natsort.natsorted(os.listdir(path)) if os.path.isdir(os.path.join(path, d))]

    def _get_list_of_files(self, path, robo):
        """
        Go through each subdirectory of `path`, and choose one file from each to use in our hash.
        Continue to increase self.iter, so we use a different 'slot' of randomness each time.
        """
        chosen_files = []

        i = 4
        hasharray = []
        if(robo is "mom"):
            hasharray = self.momhasharray
        elif(robo is "dad"):
            hasharray = self.dadhasharray
        else:
            hasharray = self.hasharray

        # Get a list of all subdirectories
        directories = []
        for root, dirs, files in natsort.natsorted(os.walk(path, topdown=False)):
            for name in dirs:
                if name[:1] is not '.':
                    directories.append(os.path.join(root, name))
                    directories = natsort.natsorted(directories)

        # Go through each directory in the list, and choose one file from each.
        # Add this file to our master list of robotparts.
        for directory in directories:
            files_in_dir = []
            for imagefile in natsort.natsorted(os.listdir(directory)):
                files_in_dir.append(os.path.join(directory,imagefile))
                files_in_dir = natsort.natsorted(files_in_dir)

            # Use some of our hash bits to choose which file
            element_in_list = hasharray[0][i] % len(files_in_dir)
            chosen_files.append(files_in_dir[element_in_list])
            i += 1
        return chosen_files

    def assemble(self,roboset=None,format=None,bgset=None,sizex=300,sizey=300, rfunc=None):
        """
        Build our Robot!
        Returns the robot image itself.
        """

        # Allow users to manually specify a robot 'set' that they like.
        # Ensure that this is one of the allowed choices, or allow all
        # If they don't set one, take the first entry from sets above.

        if roboset == 'any':
            roboset = self.sets[self.hasharray[1] % len(self.sets) ]
        elif roboset in self.sets:
            roboset = roboset
        else:
            roboset = self.sets[0]

        # Only set1 is setup to be color-seletable. The others don't have enough pieces in various colors.
        # This could/should probably be expanded at some point..
        # Right now, this feature is almost never used. ( It was < 44 requests this year, out of 78M reqs )
        # Child hasharray[a, b, c], parts_from[m, d, m]
        mom_randomcolor = self.colors[self.momhasharray[0][0] % len(self.colors)]
        dad_randomcolor = self.colors[self.dadhasharray[0][0] % len(self.colors)]

        # If they specified a background, ensure it's legal, then give it to them.
        if bgset in self.bgsets:
            bgset = bgset
        elif bgset == 'any':
            bgset = self.bgsets[self.hasharray[2] % len(self.bgsets)]

        # If we set a format based on extension earlier, use that. Otherwise, PNG.
        if format is None:
            format = self.format

        # Each directory in our set represents one piece of the Robot, such as the eyes, nose, mouth, etc.

        # Each directory is named with two numbers - The number before the # is the sort order.
        # This ensures that they always go in the same order when choosing pieces, regardless of OS.

        # The second number is the order in which to apply the pieces.
        # For instance, the head has to go down BEFORE the eyes, or the eyes would be hidden.

        # First, we'll get a list of parts of our robot.

        mom_roboparts = self._get_list_of_files(self.resourcedir + 'sets/set1/' + mom_randomcolor, "mom")
        dad_roboparts = self._get_list_of_files(self.resourcedir + 'sets/set1/' + dad_randomcolor, "dad")

        print("++++ MOM ++++")
        pp.pprint(mom_roboparts)
        print("++++ DAD ++++")
        pp.pprint(dad_roboparts)

        # Now that we've sorted them by the first number, we need to sort each sub-category by the second.
        mom_roboparts.sort(key=lambda x: x.split("#")[1])
        dad_roboparts.sort(key=lambda x: x.split("#")[1])
        roboparts = []
        for i in range(0, len(mom_roboparts)):
            if (rfunc()):
                roboparts.append(mom_roboparts[i])
            else:
                roboparts.append(dad_roboparts[i])
        if bgset is not None:
            bglist = []
            backgrounds = natsort.natsorted(os.listdir(self.resourcedir + 'backgrounds/' + bgset))
            backgrounds.sort()
            for ls in backgrounds:
                if not ls.startswith("."):
                    bglist.append(self.resourcedir + 'backgrounds/' + bgset + "/" + ls)
            background = bglist[self.hasharray[3] % len(bglist)]
        print("++++ CHILD ++++")
        pp.pprint(roboparts)
        # Paste in each piece of the Robot.
        roboimg = Image.open(roboparts[0])
        roboimg = roboimg.resize((1024,1024))
        for png in roboparts:
            img = Image.open(png)
            img = img.resize((1024,1024))
            roboimg.paste(img,(0,0),img)

        mom_roboimg = Image.open(mom_roboparts[0])
        mom_roboimg = mom_roboimg.resize((1024,1024))
        for png in mom_roboparts:
            img = Image.open(png)
            img = img.resize((1024,1024))
            mom_roboimg.paste(img,(0,0),img)

        dad_roboimg = Image.open(dad_roboparts[0])
        dad_roboimg = dad_roboimg.resize((1024,1024))
        for png in dad_roboparts:
            img = Image.open(png)
            img = img.resize((1024,1024))
            dad_roboimg.paste(img,(0,0),img)

        # If we're a BMP, flatten the image.
        if format == 'bmp':
            #Flatten bmps
            r, g, b, a = roboimg.split()
            roboimg = Image.merge("RGB", (r, g, b))

        if bgset is not None:
            bg = Image.open(background)
            bg = bg.resize((1024,1024))
            bg.paste(roboimg,(0,0),roboimg)
            roboimg = bg

        self.img = roboimg.resize((sizex,sizey),Image.ANTIALIAS)
        self.mom_img = mom_roboimg.resize((sizex,sizey),Image.ANTIALIAS)
        self.dad_img = dad_roboimg.resize((sizex,sizey),Image.ANTIALIAS)
        self.format = format
