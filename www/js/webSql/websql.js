/**
 * @singleton
 * @aside guide webSql
 * @author Copyright (c) 2016 Chen Han<gpgkd906@gmail.com>. All rights reserved
 *
 * @description
 *
 * ## Examples
 * ###
 * @example
 */
((root, factory) => {
    if (typeof exports === 'object') {
        factory(exports);
    } else if (typeof define === 'function' && define.amd) {
        define(['exports'], factory);
    } else {
        factory(root);
    }
})(this, (exports) => {
    "use strict";
    let config = {
        application: 'application',
        version: '1.0',
        db: 'websql',
        size: 50 * 1024 * 1024
    }
    , openDatabase = (exports.sqlitePlugin && exports.sqlitePlugin.openDatabase) || exports.openDatabase
    , connection = null
    , nativeConnection = null
    ;
    const setConfig = (cfg) => {
        config = cfg;
    };
    const getConfig = () => { return config; };
    const createRecordSet = (records) => {
        let offset = 0, lastId = null;
        try {
            lastId = records.insertId;
        } catch(e) {}
        return {
            fetch: () => {
                if(offset >= records.rows.length) {
                    return null;
                }
                return records.rows.item(offset++);
            },
            lastId,
            rowCount: records.rowAffected ? records.rowAffected : records.rows.length
        }
    };
    const createConnection = (nativeConnection) => {
        const defaultFunc = (...args) => { console.log(args); };
        return {
            execute: (sql, ...args) => {
                let param = [], func = null, errorFunc = null, successFunc = null;
                if(!sql) {
                    throw new Error("invalid Sql");
                }
                args.map((arg) => {
                    if(arg instanceof Array) {
                        param = arg;
                    }
                    if(arg instanceof Function) {
                        if(func === null) { func = arg; }
                        else if(errorFunc === null) { errorFunc = arg; }
                        else if(successFunc === null) { successFunc = arg; }
                    }
                });
                if(func === null) { func = defaultFunc; }
                else if(errorFunc === null) { errorFunc = defaultFunc; }
                else if(successFunc === null) { successFunc = defaultFunc; }
                nativeConnection.transaction(
                    (conn) => {
                        conn.executeSql(sql, param, (conn, result) => {
                            func.call(null, createRecordSet(result));
                        });
                    },
                    errorFunc,
                    successFunc
                );
            }
        }
    };
    const getConnection = () => {
        if(connection === null) {
            nativeConnection = openDatabase(
                config.application,
                config.version,
                config.db,
                config.size
            );
            connection = createConnection(nativeConnection);
        }
        return connection;
    };
    exports.websqlConfig = config;
    exports.close = () => {
        connection = null;
    };
    exports.getConnection = getConnection;
});
