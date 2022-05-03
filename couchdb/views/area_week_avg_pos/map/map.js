function (doc) {
    if (!doc.sentiments || !doc.geo?.suburb || !doc.geo?.geo_location?.full_name || !doc.location || !doc.user?.location) {
        // This section is to handle the historical tweet's date format
        // "Fri Jun 16 13:18:45 +0000 2017"
        /*
        var b = doc.created_at.split(/[: ]/g); 
        var m = {jan:0, feb:1, mar:2, apr:3, may:4, jun:5, jul:6,
                 aug:7, sep:8, oct:9, nov:10, dec:11};
      
        var date = new Date(Date.UTC(b[7], m[b[1].toLowerCase()], b[2], b[3], b[4], b[5]));
        */
        
        // 2022-04-30 21:21:31+00:00
        var b = doc.created_at.split(/[-: /+]/g)
        var date = new Date(Date.UTC(b[0], b[1], b[2], b[3], b[4], b[5]));

        //#region Getting which week of the year
        date.setHours(0, 0, 0, 0);

        // Thursday in current week decides the year.
        date.setDate(date.getDate() + 3 - (date.getDay() + 6) % 7);
        var week1 = new Date(date.getFullYear(), 0, 4);
        week_of_year = 1 + Math.round(((date.getTime() - week1.getTime()) / 86400000 - 3 + (week1.getDay() + 6) % 7) / 7);
        week_of_year_str = `w${week_of_year}-${b[7]}` // "w24-2017"
        //#endregion
    
        //#region Getting the location/ suburb name
        var location = "none";

        if (!doc.geo?.suburb) {
            location = doc.geo.suburb.trim().toLowerCase();
        }
        else if (!doc.geo?.geo_location?.full_name) {
            full_name = doc.geo?.geo_location?.full_name // "Rajasthan, India"
            location = full_name.split(',')[0].trim().toLowerCase();
        }
        else if (!doc.location) {
            location = doc.location.trim().toLowerCase()
        }
        else if (!doc.user?.location) {
            // Get the location from user's profile
            location = doc.user.location.trim().toLowerCase()
        }
        else if (!doc.city_rule_key) {
            location = doc.city_rule_key.trim().toLowerCase()
        }
        //#endregion

        emit([week_of_year_str, location], doc.sentiments.pos);
    }
}