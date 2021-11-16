
# Create Command

* Method type: POST
* CMD value: "create"
* Request payload fields:
	* "cmd" - equal to "create"
	* "path" - path to new object
	* "type" - object to create
		* Accepted values: "file" or "folder"
* Response payload fields (for success):
	* "client_cmd" - equal to "create"
	* "status" - status of the operation
		* Accepted value: "created" or "exists"
* Responses:
	* 2.04 Changed - object was created, or an existing one was found
	* 4.04 Not Found - path is not valid
	* 4.03 Forbidden - action was denied by file system (missing file perms, etc.)
* Request payload samples:
	```
	{
		"cmd": "create",
		"path": "/users/Alex/docs/readme.md",
		"type": "file"
	}
	```
* Response payload samples:
	```
	// 1 - 2.04 Changed - object created
	{
		"client_cmd": "create",
		"status": "created"
	}
	// 2 - 2.04 Changed - object already exists
	
	{
		"client_cmd": "create",
		"status": "exists"
	}
	// 3 - 4.04 Not Found - diagnostic message
	"Path is invalid"
	// 4 - 4.03 Forbidden - diagnostic message
	"Missing file permissions for target object"
	```


# Open Command

* Method Type: GET
* CMD value: "open"
* Request payload fields:
	* "cmd" - equal to "open"
	* "path" - path to file
* Response payload fields (for success):
	* "client_cmd" - equal to "open"
	* "response" - contents of the file
* Responses:
	* 2.05 Content - contains the file data
	* 4.04 Not Found - path is not valid
	* 4.03 Forbidden - action was denied by file system (missing file perms, etc.)
* Request payload samples:
	```
    	{
		"cmd": "open",
		"path": "/users/Alex/docs/readme.md"
	}
	```
* Response payload samples:
	```
	// 1 - 2.05 Content - file retrieved
	{
		"client_cmd": "open",
		"response": "This is a readme file for the CoAP Server repository"
	}
	// 2 - 4.04 Not Found - diagnostic message
	"Path is invalid"
	// 3 - 4.03 Forbidden - diagnostic message
	"Missing file permissions for target object"
	```


# Save Command

* Method Type: POST
* CMD value: "save"
* Request payload fields:
	* "cmd" - equal to "save"
	* "path" - path to new object
	* "content" - new file contents (size limited by MTU)
* Response payload fields (for success):
	* "client_cmd" - equal to "save"
	* "status" - status of the operation
		* Accepted fields: "modified"
* Responses:
	* 2.04 Changed - the file was modified
	* 4.04 Not Found - path is not valid
	* 4.03 Forbidden - action was denied by file system (missing file perms, etc.)
* Request payload samples:
    	```
	{
		"cmd": "save",
		"path": "/users/Alex/docs/readme.md",
		"content": "This is a readme file for the CoAP Server repository"
	}
	```
* Response payload samples:
	```
	// 1 - 2.04 Changed - file modified
	{
		"client_cmd": "save",
		"status": "modified"
	}
	// 2 - 4.04 Not Found - diagnostic message
	"Path is invalid"
	// 3 - 4.03 Forbidden - diagnostic message
	"Missing file permissions for target object"
	```


# Delete Command

* Method Type: POST
* CMD value: "delete"
* Request payload fields:
	* "cmd" - equal to "delete"
	* "path" - path to existing object
* Response payload fields (for success):
	* "client_cmd" - equal to "delete"
	* "status" - status of the operation
		* Accepted fields: "deleted file", "deleted folder", "missing"
* Responses:
	* 2.02 Deleted - the file was deleted, or file was missing (but preceding path was OK)
	* 4.04 Not Found - path is not valid
	* 4.03 Forbidden - action was denied by file system (missing file perms, etc.)
* Request payload samples:
	```
    	{
		"cmd": "delete",
		"path": "/users/Alex/docs/readme.md"
	}
	```
* Response payload samples:
	```
	// 1 - 2.02 Deleted - file deleted
	{
		"client_cmd": "delete",
		"status": "deleted file"
	}
	// 2 - 4.04 Not Found - diagnostic message
	"Path is invalid"
	// 3 - 4.03 Forbidden - diagnostic message
	"Missing file permissions for target object"
	```
	

# Rename Command

* Method Type: POST
* CMD value: "rename"
* Request payload fields:
	* "cmd" - equal to "rename"
	* "path" - path to existing object
	* "name" - the new name of the object
* Response payload fields (for success):
	* "client_cmd" - equal to "rename"
	* "status" - status of the operation
		* Accepted fields: "renamed"
* Responses:
	* 2.04 Changed - the file was renamed
	* 4.04 Not Found - path is not valid
	* 4.03 Forbidden - an object with the new name already exists
	* 4.03 Forbidden - action was denied by file system (missing file perms, etc.)
* Request payload samples:
	```
    	{
		"cmd": "rename",
		"path": "/users/Alex/docs/readme.md"
	}
	```
* Response payload samples:
	```
	// 1 - 2.04 Changed - file renamed
	{
		"client_cmd": "rename",
		"status": "renamed"
	}
	// 2 - 4.04 Not Found - diagnostic message
	"Path is invalid"
	// 3 - 4.03 Forbidden - diagnostic message
	"Missing file permissions for target object"
	// or...
	"An object with that name already exists"
	```


# Move Command

* Method Type: POST
* CMD value: "move"
* Request payload fields:
	* "cmd" - equal to "move"
	* "path" - path to existing object
	* "new_path" - the new path of the object
* Response payload fields (for success):
	* "client_cmd" - equal to "move"
	* "status" - status of the operation
		* Accepted fields: "moved"
* Responses:
	* 2.04 Changed - the file was moved
	* 4.04 Not Found - path is not valid
	* 4.04 Not Found - new_path is not valid
	* 4.03 Forbidden - an object with the new path already exists
	* 4.03 Forbidden - action was denied by file system (missing file perms, etc.)
* Request payload samples:
	```
    	{
		"cmd": "rename",
		"path": "/users/Alex/docs/readme.md"
	}
	```
* Response payload samples:
	```
	// 1 - 2.04 Changed - file moved
	{
		"client_cmd": "move",
		"status": "moved"
	}
	// 2 - 4.04 Not Found - diagnostic message
	"Path is invalid"
	// or...
	"New path is invalid"
	// 3 - 4.03 Forbidden - diagnostic message
	"Missing file permissions for target object"
	// or...
	"An object with that name already exists"
	```
	

# Details Command

* Method Type: GET
* CMD value: "details"
* Request payload fields:
	* "cmd" - equal to "details"
	* "path" - path to existing object
* Response payload fields (for success):
	* "client_cmd" - equal to "details"
	* "path" - the path of the object (echoed from request)
	* "type" - object type
		* Accepted values: "file", "folder"
	* "dir_contents" - list of object names in the directory
		* Only present if "type" = "folder"
	* "size" - size of the object in bytes
* Responses:
	* 2.05 Content - the details of the object
	* 4.04 Not Found - path is not valid
	* 4.03 Forbidden - action was denied by file system (missing file perms, etc.)
* Request payload samples:
    	```
	{
		"cmd": "details",
		"path": "/users/Alex/docs/readme.md"
	}
	// or...
	{
		"cmd": "details",
		"path": "/users/Alex/docs"
	}
	```
* Response payload samples:
	```
	// 1 - 2.05 Content - asked about a file
	{
		"client_cmd": "details",
		"path": "/users/Alex/docs/readme.md",
		"type": "file",
		"size": 1337420
	}
	// 2 - 2.05 Content - asked about a folder
	{
		"client_cmd": "details",
		"path": "/users/Alex/docs",
		"type": "folder",
		"size": 1337420133,
		"dir_contents": [ "readme.md", "mods.dll", "Half_Life_3.exe", "MyMusic", "backups" ]
	}
	// 3 - 4.04 Not Found - diagnostic message
	"Path is invalid"
	// 4 - 4.03 Forbidden - diagnostic message
	"Missing file permissions for target object"
	```
	
	
# Search Command
* Method Type: SEARCH (special method)
* Request payload fields:
	* "path" - where to search
	* "target_name_regex" - a regex which targets should match
* Response payload fields (for success):
	* "search_path" - the path sent in the response
	* "results" - a list of matching objects
	* "result_paths" - the absolute paths of the matching objects
* Responses:
	* 2.05 Content - the results of the search
	* 4.04 Not Found - path is not valid
	* 4.03 Forbidden - action was denied by file system (missing file perms, etc.)
* Request payload samples:
    	```
	{
		"path": "/users/Alex",
		"target_name_regex": "*.exe"
	}
	```
* Response payload samples:
	```
	// 1 - 2.05 Content - search results
	{
		"search_path": "/users/Alex",
		"results": [ "lmao.exe", "Half_Life_3.exe" ],
		"result_paths": [ "/users/Alex/lmao.exe", "/users/Alex/docs/Half_Life_3.exe" ]
	}
	// 3 - 4.04 Not Found - diagnostic message
	"Search path is invalid"
	// 4 - 4.03 Forbidden - diagnostic message
	"Missing file permissions for searching"
	```
	
