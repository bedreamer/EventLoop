# webSql

##example 
```javascript
websqlConfig.application = "myApp";  
websqlConfig.db = "myDb";  
websqlConfig.size = 100 * 1024 * 1024;

var connection = getConnection();

connection.execute("CREATE TABLE IF NOT EXISTS users (id integer primary key autoincrement, name text, age integer)");

connection.execute("INSERT INTO users (name, age) VALUES ('zhao', 20), ('wang', 25), ('sun', 30), ('li', 35)", (stmt) => {  
	console.log(stmt.lastId);  
});

connection.execute("SELECT * FROM users WHERE name = ?", ['wang'], (stmt) => {  
  	while(record = stmt.fetch()) {  
  		console.log(record);  
  	}  
});
```