module.exports = function (grunt) {
  grunt
    .initConfig({
      "couch-compile": {
        dbs: {
          files: {
            "/tmp/twitter.json": "couchdb/twitter/language"
          }
        }
      },
      "couch-push": {
        options: {
          user: process.env.user,
          pass: process.env.pass
        },
        twitter: {
        }
      }
    });

  grunt.config.set(`couch-push.twitter.files.http://localhost:5984/${process.env.dbname}`, "/tmp/twitter.json");
console.log(JSON.stringify(grunt.config.get()));
  grunt.loadNpmTasks("grunt-couch");
};
