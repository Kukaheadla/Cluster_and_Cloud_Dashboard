function a(doc) {
    if (!doc.geo?.suburb || !doc.geo?.geo_location?.full_name || !doc.location || !doc.user?.location) {
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

        print([week_of_year_str, location], doc);
    }
}

t = {
    "_id": "1521139073355685890",
    "_rev": "1-fdd2de002a148ad5b74d5e3671097720",
    "reply_settings": "everyone",
    "entities": {
      "urls": [
        {
          "start": 186,
          "end": 209,
          "url": "https://t.co/mYpxzrBSKh",
          "expanded_url": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=1822004",
          "display_url": "pib.gov.in/PressReleasePa…"
        },
        {
          "start": 210,
          "end": 233,
          "url": "https://t.co/GrDg8Ovxj7",
          "expanded_url": "https://twitter.com/dtytrivedi/status/1521139073355685890/photo/1",
          "display_url": "pic.twitter.com/GrDg8Ovxj7"
        },
        {
          "start": 210,
          "end": 233,
          "url": "https://t.co/GrDg8Ovxj7",
          "expanded_url": "https://twitter.com/dtytrivedi/status/1521139073355685890/photo/1",
          "display_url": "pic.twitter.com/GrDg8Ovxj7"
        },
        {
          "start": 210,
          "end": 233,
          "url": "https://t.co/GrDg8Ovxj7",
          "expanded_url": "https://twitter.com/dtytrivedi/status/1521139073355685890/photo/1",
          "display_url": "pic.twitter.com/GrDg8Ovxj7"
        },
        {
          "start": 210,
          "end": 233,
          "url": "https://t.co/GrDg8Ovxj7",
          "expanded_url": "https://twitter.com/dtytrivedi/status/1521139073355685890/photo/1",
          "display_url": "pic.twitter.com/GrDg8Ovxj7"
        }
      ]
    },
    "source": "Twitter Web App",
    "attachments": {
      "media_keys": [
        "3_1521138182644854786",
        "3_1521138242745032704",
        "3_1521138310705426433",
        "3_1521138476413947904"
      ]
    },
    "possibly_sensitive": false,
    "created_at": "2022-05-02 14:46:31+00:00",
    "author_id": 137364924,
    "conversation_id": 1521139073355686000,
    "id": 1521139073355686000,
    "public_metrics": {
      "retweet_count": 0,
      "reply_count": 1,
      "like_count": 0,
      "quote_count": 0
    },
    "text": "Trichy Airport undergoing upgradation to offer better services\n\nThe terminal will be an energy efficient building with sustainable features\n\nTrichy terminal will be ready by April 2023\n\nhttps://t.co/mYpxzrBSKh https://t.co/GrDg8Ovxj7",
    "lang": "en",
    "day_of_week": "Monday",
    "year": "2022",
    "month": "05",
    "day": "02",
    "hour": "14",
    "city_rule_key": "melbourne",
    "topic_name": "environment",
    "overall_sentiment": "neutral_sentiment",
    "sentiments": {
      "neg": 0,
      "neu": 0.691,
      "pos": 0.309,
      "compound": 0.8519
    }
}
a(t)
