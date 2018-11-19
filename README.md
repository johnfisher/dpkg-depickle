# dpkg-depickle
Th utility was written for a Linux-based network switch. We needed to be able to tell whether packages had been changed on the system compared to well-known manifests.  The utility could also diff two 'dpkg -l' outputs in a useful way, so that system configurations could be compared from one host to another. ( this was all long before DevOps)

It needs to run as root.

# ./dpkg-depickle.py [filename][filename]

no args:  looks for previously created local manifest in current directory. See sample manifest in project. Compares localhost against manifest.
one filename arg:  compares local manifest against filename
two filename args: compares two manifest files

files must be in dpkg -l > outfile  format

typical output:
# ./dpkg-depickle.py
   ... Manifest directory .

## Using this manifest file: 1.2.3.x-oa4-x.manifest ##

--------------------------------------------------------------------
## Packages missing in LOCAL system, but listed in 1.2.3.x-oa4-x.manifest ##
    none.
--------------------------------------------------------------------
## Packages on LOCAL system, but missing in 1.2.3.x-oa4-x.manifest ##
  aisleriot 
  akonadi-backend-mysql 
  akonadi-server 
  alacarte 
  alien 
  alsa-base 
  alsa-utils 
  amd64-microcode 
  anacron 
  apache2 
  apg 
--------------------------------------------------------------------
## Packages in with a different version  ##
  LOCAL VERSION                            1.2.3.x-oa4-x.manifest VERSION           
    none.
    
    
