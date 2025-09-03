# fastAPI_repo_template
My default template for fastAPI projects

The docker-compose.example and .env.example files are the compose and env from a project of mine, used as examples of how to build you project compose using both variables (for multiple dockers), a DB (in my case MariaDB) and compose. Both files, if used, should be on the main dir with the microservices, as:  

Project_Folder  
--Docker-compose  
--.env  
--microservice1 (repository)  
----dockerfile  
----etc...  
--microservice2 (repository)  
----dockerfile  
----etc...  
--microservice3 (repository)  
----dockerfile  
----etc...  

