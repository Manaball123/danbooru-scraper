
#dir format:
#./anime-porn/database/1(1 % 100 = 1)/1.json
#each json contains 1000 entries, merged


#required info:
#id - uint32
#md5 - int128(16 bytes)
#tag_string - string
#score - int32
#(optional: up_score/down_score) - int32
#file_size - uint32
#file_ext - char[3]/int8
#NOTE: NO I AM NOT SAVING FILE URL BECAUSE I CAN REASSEMBLE IT EZPZ
#file_url(and/or large_file_url) - string
#large_file_url(refer 2 above)
#NOTE: large_file_url usually isnt present so I don't think it is really needed
#worse case scenario we check md5 and pick the correct one


#this just scrapes a json for now, see the other repo for more deets




