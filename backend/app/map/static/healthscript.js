
$('#injuryform').keydown(function(e) {
  var key = e.which;
  if (key == 13) {
    // As ASCII code for ENTER key is "13"
    loadData(); // Submit form code
  }
});

$('#locationform').keydown(function(e) {
  var key = e.which;
  if (key == 13) {
    // As ASCII code for ENTER key is "13"
    loadData(); // Submit form code
  }
});

function loadData() {
  var symptom = document.getElementById('injuryform').value;
  var location = document.getElementById('locationform').value;
  $.getJSON('/getLocations?symptom=' + symptom + "&location=" + location, function(data) {
      //data is the JSON string
      putLocationsOnMap(data);
  });
}



var currentMarkers = [];
function  putLocationsOnMap(data) {
  document.getElementById('infocard').style.zIndex = 9999;
  var dngtitle = document.getElementById('dngtitle');
  dngtitle.innerText = data.drg;

  map.setCenter({lat: data.center.lat, lng: data.center.lng});
  //remove currentMarkers
  for(var i = 0; i < currentMarkers.length; i++) {
    currentMarkers[i].setMap(null);
    currentMarkers[i] = null;
  }
  currentMarkers = [];

  var tablebody = document.getElementById('tablebody');
  while(tablebody.firstChild) {
    tablebody.removeChild(tablebody.firstChild);
  }

  var foundHospitals = data.hospitals;
  foundHospitals.sort(function(a,b) { return (a.cover-a.payment)-(b.cover-b.payment) });

  for(var i = 0; i < foundHospitals.length; i++) {
    //add marker on map
    currentMarkers.push(new google.maps.Marker({
      position: new google.maps.LatLng(foundHospitals[i].lat,foundHospitals[i].lng),
      animation: google.maps.Animation.DROP,
      title: foundHospitals[i].name
    }));
    currentMarkers[i].setMap(map);

    //add row to table
    var tr = document.createElement("tr");
    var th = document.createElement("th");
    th.setAttribute("scope","row");
    th.innerText = i+1;
    var nameCell = document.createElement("td");
    nameCell.innerText = foundHospitals[i].name;
    var addressCell = document.createElement("td");
    addressCell.innerText = foundHospitals[i].addr;
    var oopCell = document.createElement("td");
    oopCell.innerText = "$" + Math.round((foundHospitals[i].cover - foundHospitals[i].payment)*100)/100;
    tr.appendChild(th);
    tr.appendChild(nameCell);
    tr.appendChild(addressCell);
    tr.appendChild(oopCell);
    tablebody.appendChild(tr);

  }

}
