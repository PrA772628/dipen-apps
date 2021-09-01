
function openModal() {
	$("#uploadFileModal li").first().children()[0].click();
}
function showPickerDialog() {
	loadPicker()
}

$(document).ready(function () {
	var drive_api = $('#drive-api-key').val();
	var drive_client_id = $('#drive-client-id').val();
	var drive_project_id = $('#drive-project-id').val();
	var dropbox_api_key = $('#dropbox-api-key').val();
	var onedrive_app_id = $('#onedrive-app-id').val();

	const script = document.createElement("script");
	script.type = "text/javascript";
	script.src = "https://www.dropbox.com/static/api/2/dropins.js";
	script.id = "dropboxjs";
	script.setAttribute('data-app-key', String(dropbox_api_key))
	script.async = true;
	script.dataset.cfasync = false;
	document.body.appendChild(script);
	script.addEventListener("load", () => {
	});

	var check_list = []
	var selected_files = []
	/* --------------------------------------------------------------------------------------------------
									google picker
	-------------------------------------------------------------------------------------------------- */
	var developerKey = String(drive_api);

	// The Client ID obtained from the Google API Console. Replace with your own Client ID.
	var clientId = String(drive_client_id);

	// Replace with your own project number from console.developers.google.com.
	// See "Project number" under "IAM & Admin" > "Settings"
	var appId = String(drive_project_id);

	// Scope to use to access user's Drive items.
	var scope = ['https://www.googleapis.com/auth/drive.file'];

	var pickerApiLoaded = false;
	var oauthToken;

	window.loadPicker = function () {
		gapi.load('auth', { 'callback': onAuthApiLoad });
		gapi.load('picker', { 'callback': onPickerApiLoad });
	}

	function onAuthApiLoad() {
		window.gapi.auth.authorize(
			{
				'client_id': clientId,
				'scope': scope,
				'immediate': false
			},
			handleAuthResult);
	}

	function onPickerApiLoad() {
		pickerApiLoaded = true;
		createPicker();
	}

	function handleAuthResult(authResult) {
		if (authResult && !authResult.error) {
			oauthToken = authResult.access_token;
			createPicker();
		}
	}

	function createPicker() {
		if (pickerApiLoaded && oauthToken) {
			var view = new google.picker.View(google.picker.ViewId.DOCS);
			view.setMimeTypes("image/png,image/jpeg,image/jpg,application/pdf,application/msword,application/vnd.google-apps.document");
			var picker = new google.picker.PickerBuilder()
				.enableFeature(google.picker.Feature.NAV_HIDDEN)
				.enableFeature(google.picker.Feature.MULTISELECT_ENABLED)
				.setAppId(appId)
				.setOAuthToken(oauthToken)
				.addView(view)
				.addView(new google.picker.DocsUploadView())
				.setDeveloperKey(developerKey)
				.setCallback(pickerCallback)
				.build();
			picker.setVisible(true);
		}
	}

	function pickerCallback(data) {
		if (data[google.picker.Response.ACTION] == google.picker.Action.PICKED) {
			var doc = data[google.picker.Response.DOCUMENTS];
			doc.forEach(function (file) {
				if (check_list.includes(file.name)) {
				} else {
					add_img_to_list(file);
					check_list.push(file.name);
					selected_files.push(file);
				}
			});
		}
	}



	/* --------------------------------------------------------------------------------------------------
									dropbox picker
	-------------------------------------------------------------------------------------------------- */



	$('.btn-dropbox').click(function () {
		var options = {
			success: function (files) {
				files.forEach(function (file) {
					if (check_list.includes(file.name)) {
					} else {
						add_img_to_list(file);
						check_list.push(file.name);
						selected_files.push(file);
					}
				});
			},
			cancel: function () {
			},
			linkType: "preview",
			multiselect: true,
			extensions: ['.pdf', '.doc', '.docx', '.html', '.png', '.jpg', '.jpeg', '.svg', '.csv', '.dochtml', '.pages', '.pdfxml', '.pdfhtml', '.template', '.txt', '.xlr', '.xls', '.xlsx',],
		};
		Dropbox.choose(options);
	});

	/* --------------------------------------------------------------------------------------------------
									onedrive picker
	-------------------------------------------------------------------------------------------------- */

	$('.btn-onedrive').click(function () {
		var odOptions = {
			clientId: String(onedrive_app_id),
			action: "download",
			multiSelect: true,
			advanced: {
			},
			success: function (files) {
				files.value.forEach(function (file) {
					if (check_list.includes(file.name)) {
					} else {
						add_img_to_list(file);
						check_list.push(file.name);
						selected_files.push(file);
					}
				});
			},
			cancel: function () { /* cancel handler */ },
			error: function (error) { /* error handler */ }
		};

		OneDrive.open(odOptions);
	});


	/* --------------------------------------------------------------------------------------------------
									device picker
	-------------------------------------------------------------------------------------------------- */

	const fileInput = document.querySelector(".file-input");

	// form click event


	$("html").on("dragover", function (e) {
		e.preventDefault();
		e.stopPropagation();
	});

	$("html").on("drop", function (e) { e.preventDefault(); e.stopPropagation(); });

	// Drag enter
	$('.device-area').on('dragenter', function (e) {
		e.stopPropagation();
		e.preventDefault();
	});


	// Drop
	$('.device-area').on('drop', function (e) {
		e.stopPropagation();
		e.preventDefault();


		var files = e.originalEvent.dataTransfer.files;
		for (var [key, value] of Object.entries(files)) {
			if (check_list.includes(value.name)) {
			} else {
				add_img_to_list(value);
				check_list.push(value.name);
				selected_files.push(value);
			}
		}
		//calling uploadFile with passing file name as an argument
	});

	$('.device-area').click(function () {
		fileInput.click();
	});


	fileInput.onchange = ({ target }) => {
		let files = target.files; //getting file [0] this means if user has selected multiple files then get first one only


		for (var [key, value] of Object.entries(files)) {
			if (check_list.includes(value.name)) {
			} else {
				add_img_to_list(value);
				check_list.push(value.name);
				selected_files.push(value);
			}
		} //calling uploadFile with passing file name as an argument
	}


	function add_img_to_list(file) {

		image_ext = ['png', 'jpg', 'jpeg', 'svg']
		file_ext = ['pdf', 'doc', 'docx', 'csv', 'txt', 'xls', 'xlsx',]
		const check_ext = file.name.split(".");
		console.log(file)
		if (image_ext.includes(check_ext[1])) {
			var newnode = document.createElement('div');
			newnode.className = 'image-item';
			newnode.style.backgroundColor = "#eee";
			newnode.style.marginTop = "15px";


			var img = new Image();
			var src = file.thumbnailLink || file["@microsoft.graph.downloadUrl"] || "https://drive.google.com/uc?export=view&id=" + String(file.id) || URL.createObjectURL(file);
			src = src.replace("bounding_box=8");
			src = src.replace("mode=fit", "mode=crop");
			img.className = "select-image";
			img.src = src;
			img.width = "60";
			img.height = "60";
			img.style.margin = "10px 10px 10px 10px";


			var img_name = document.createElement('span');
			img_name.className = "img-name";
			img_name.textContent = file.name;
			img_name.style.fontWeight = "700";
			img_name.style.margin = "10px 10px 10px 10px";


			var cancel_button = document.createElement('button');
			cancel_button.className = "cancel";
			cancel_button.type = "button";
			var span = document.createElement('span');
			span.textContent = "×";
			span.className = "cancel";
			span.style.margin = "12px 26px 12px 26px";
			span.style.fontSize = "30px";
			span.style.color = "#696969";
			span.style.display = "flex";
			span.style.transition = "all 0.2s ease-out";
			cancel_button.style.border = "0px";
			cancel_button.style.float = "right";
			cancel_button.style.outline = "0px";

			cancel_button.appendChild(span);
			newnode.appendChild(img);
			newnode.appendChild(img_name);
			newnode.appendChild(cancel_button);

			document.getElementById("image-show").appendChild(newnode);
			$('.cancel').click(function () {
				$(this).parent().parent().remove();
			});
		} else {
			var newnode = document.createElement('div');
			newnode.className = 'image-item';
			newnode.style.backgroundColor = "#eee";
			newnode.style.marginTop = "15px";
			newnode.style.height = "70px";

			var seconenode = document.createElement('div');
			seconenode.className = "file-icon";
			seconenode.style.borderRadius = "30px";
			seconenode.style.display = "flex";
			seconenode.style.alignItems = "center";
			// seconenode.style.webkitBoxAlign = "center";
			seconenode.style.justifyContent = "center";
			seconenode.style.minWidth = "58px";
			seconenode.style.height = "60px";
			seconenode.style.background = "white";
			seconenode.style.margin = "5px 10px 5px 10px"
			seconenode.style.float = "left";

			alert(file)
			var img = new Image();
			if (check_ext[1] === "pdf") {
				var src = "/file_picker/static/src/img/pdf.png";
			}
			else if (check_ext[1] === "doc") {
				var src = "/file_picker/static/src/img/doc.png";
			}
			else if ((check_ext[1] === "docx") || (file.serviceId == "doc")){
				var src = "/file_picker/static/src/img/docx.png";
			}
			else if (check_ext[1] === "txt") {
				var src = "/file_picker/static/src/img/txt.png";
			}
			else if (check_ext[1] === "csv") {
				var src = "/file_picker/static/src/img/csv.png";
			}
			else if (check_ext[1] === "xls") {
				var src = "/file_picker/static/src/img/xls.png";
			}

			src = src.replace("bounding_box=8");
			src = src.replace("mode=fit", "mode=crop");
			img.className = "select-image";
			img.src = src;
			img.width = "40";
			img.height = "40";
			img.style.margin = "10px 10px 10px 10px";


			seconenode.appendChild(img);

			var file_name = document.createElement('span');
			file_name.className = "file-name";
			file_name.textContent = file.name;
			file_name.style.float = "left";
			file_name.style.fontWeight = "700";
			file_name.style.margin = "25px 0px 15px 10px";


			var cancel_button = document.createElement('button');
			cancel_button.className = "cancel";
			cancel_button.type = "button";
			var span = document.createElement('span');
			span.textContent = "×";
			span.className = "cancel";

			span.style.margin = "12px 26px 11px 26px";
			span.style.fontSize = "30px";
			span.style.color = "#696969";
			span.style.display = "flex";
			span.style.transition = "all 0.2s ease-out";
			cancel_button.style.border = "0px";
			cancel_button.style.float = "right";
			cancel_button.style.outline = "0px";
			cancel_button.appendChild(span);

			newnode.appendChild(seconenode);
			newnode.appendChild(file_name);
			newnode.appendChild(cancel_button);

			document.getElementById("files-show").appendChild(newnode);
			$('.cancel').click(function () {
				var text1=$(this).parent().parent().text().slice(0, -1);
				for( var i = 0; i < selected_files.length; i++){ 
    
					if ( selected_files[i].name == text1) { 
				
						selected_files.splice(i, 1); 
					}
				
				}
				$(this).parent().parent().remove();

			});
		}
		console.log(selected_files)
	}
	
});