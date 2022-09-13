function htmlCollectionToArray(collection) {
  result = [];
  for (i = 0; i < collection.length; i++) {
    result.push(collection[i]);
  }
  return result;
}

videoDictionary = {};
categories = {};
for (video of videos) {
  category = (categories.hasOwnProperty(video.series) ? categories[video.series] : []);
  category.push(video);
  categories[video.series] = category;

  videoDictionary[video.shortname] = video;
}

sortedCategoryKeys = Array.from(Object.keys(categories)).sort();

currentlySelectedCategory = null;

selectCategory(sortedCategoryKeys[0]);

writeFooter();

function showVideo(video) {
  playerBackground = document.getElementById("player-background");

  playerBackground.style.visibility = "visible";

  // create the close button
  closeButton = document.createElement("span");
  closeButton.setAttribute("id", "closeVideo");
  closeButton.setAttribute("class", "buttons");
  closeButton.innerHTML = "×";
  closeButton.onclick = function(e) {
    document.getElementById("player-background").innerHTML = "";
    document.getElementById("player-background").style.visibility = "hidden";
  }
  playerBackground.appendChild(closeButton);

  // create the video element
  videoElement = document.createElement("video");
  videoElement.setAttribute("controls", "");
  videoElement.setAttribute("autoplay", "");
  videoElement.setAttribute("id", "video");
  playerBackground.appendChild(videoElement);

  // create the source element
  sourceElement = document.createElement("source");
  sourceElement.setAttribute("src", video.video);
  videoElement.appendChild(sourceElement);

  // create the mediathekviewweb link
  linkElement = document.createElement("a");
  linkElement.setAttribute("class", "mediathekviewweblink");
  linkElement.setAttribute("target", "_blank");
  linkElement.setAttribute("href", "http://mediathekviewweb.de/#query=" + video.series + " " + video.title);
  linkElement.innerHTML = "MediathekViewWeb";
  playerBackground.appendChild(linkElement);
}

function writeFooter() {
  // Show the footer only if it actually contains something.
  if (categories.length <= 1) {
    return;
  }
  document.write("<div id=\"footer\">")
  document.write("<span class=\"helper\"></span>")
  for (category of Array.from(Object.keys(categories)).sort()) {
    if (category != "") {
      document.write("<img class=\"categoryPicture\" title=\"" + category + "\" src=\"assets/category%20pictures/" + category + ".png\" onclick='selectCategory(\"" + category + "\")'>")
    }
  }
  document.write("</div>");
}

function selectCategory(desiredCategory) {
  if (currentlySelectedCategory == desiredCategory) {
    return;
  }

  currentlySelectedCategory = desiredCategory;
  rootElement = document.getElementById("video-list-container");

  // write the videos
  html = "";
  html += "<h1>" + desiredCategory + "</h1>";

  html += "<ul>";
  for (link of pageLinks[desiredCategory]) {
    html += "<li><a href=\"" + link + "\">" + link + "</a></li>";
  }
  html += "</ul>";

  html += "<ul class=\"thumbnails\">";
  for (video of categories[desiredCategory]) {
    type = video.type;
    line = '<li class="Video" id="' + video.shortname + '"><a href="' + video.video + '">';
    line += '<img ';
    line += type == "UnavailableVideo" ? 'class="unavailable" ' : "";
    line += 'src="' + video.img + '"><br>';
    line += '<span';
    line += type == "NotHotlinkableVideo" ? ' class="nothotlinkable"' : '';
    line += '>' + video.title;
    line += '</span></a></li>';
    html += line;
  }
  html += "</ul>";

  rootElement.innerHTML = html;

  // attach event
  for (video of htmlCollectionToArray(document.getElementsByClassName("Video"))) {
    if (video.getElementsByTagName("img")[0].className == "unavailable") {
      continue;
    }
    if (video.getElementsByTagName("span")[0].className == "nothotlinkable") {
      continue;
    }

    video.onclick = function(e) {
      e.preventDefault();
      elm = e.target;

      // Bubble up to find LI from the current element.
      while (true) {
        if (elm.nodeName == "LI")
          break;
        else
          elm = elm.parentElement;
      }

      videoObject = videoDictionary[elm.id];

      showVideo(videoObject);
    };
  }
}

