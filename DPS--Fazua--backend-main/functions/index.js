const functions = require("firebase-functions");
const fs = require('fs');
const path = require('path');
const cors = require("cors")({ origin: true });
const https = require("https");
const Busboy = require('busboy');
// const axios = require("axios").default;
// const qs = require("qs");

// // Create and Deploy Your First Cloud Functions
// // https://firebase.google.com/docs/functions/write-firebase-functions
//
// exports.helloWorld = functions.https.onRequest((request, response) => {
//   functions.logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });

// TODO
// CAPTURE THE AUTH_TOKEN FROM THE BROWSER
// CREATE ROUTES ON THE KOMOOT APP
// DO komoot call for the user to gpx files
// Display everything on the console
// to solve the null key is to get all keys from the data

const config = functions.config(); // ENV configuration for Firebase, set via https://firebase.google.com/docs/functions/config-env
const komootBaseUrl = "https://auth-api.main.komoot.net/oauth";
const komootAuthUrl = komootBaseUrl + "/authorize";
const komootTokenUrl = komootBaseUrl + "/token";

const komootClientId = config.komoot.clientid;
const komootClientSecret = config.komoot.clientsecret;

const oAuthSuccessUrl =
	"https://europe-west3-fazua-dps.cloudfunctions.net/authSuccess";
	// "http://localhost:5001/fazua-dps/europe-west3/authSuccess"; // (url for local emulator)

/* const accessTokenSuccessUrl =
    //  "https://europe-west3-fazua-dps.cloudfunctions.net/accessTokenSuccess";
    "http://localhost:5001/fazua-dps/europe-west3/accessTokenSuccess"; // (url for local emulator) */

/* exports.receiveToken = functions
	.region("europe-west3")
	.https.onRequest((req, res) => {
		cors(req, res, () => {
			console.log("We've received a token");
		});
	}); */

exports.tourFile = functions
	.region("europe-west3")
	.https.onRequest((req, res) => {
		cors(req, res, () => {
			const busboy = new Busboy({headers : req.headers});
			const uploads = {};
			const filewrites = [];
			busboy.on('file', (fieldname, file, filename) => {
				const filepath = path.join(__dirname, filename);
				uploads[filename] = filepath;

				const writeStream = fs.createWriteStream(filepath);
				file.pipe(writeStream);


				const promise = new Promise((resolve, reject) => {
					file.on('end', () => {
						writeStream.end();
					});
					writeStream.on('finish', resolve);
					writeStream.on('error', reject);
				});
				filewrites.push((promise))
			});
			busboy.on('finish', async () => {
				await Promise.all(filewrites);
				// Process files here
				res.send("Files are uploaded successfully");
			});
			busboy.end(req.rawBody);
		});
	});

exports.authSuccess = functions
	.region("europe-west3")
	.https.onRequest((req, res) => {
		cors(req, res, () => {
			// 1) You get the `code` parameter as a query parameter
			const authCode = req.query.code;
			// 2) Request an actual auth token from the API via a POST request
			const request = https.request(
				`${komootTokenUrl}?redirect_uri=${encodeURIComponent(
					oAuthSuccessUrl
				)}&grant_type=authorization_code&code=${authCode}`,
				{
					method: "POST",
					headers: {
						Accept: "application/json",
						Authorization: `Basic ${Buffer.from(
							komootClientId + ":" + komootClientSecret
						).toString("base64")}`,
					},
				},
				(response) => {
					// 3) Do something with the Auth Token, i.e. send it on to your app or directly do a request to the User API from Komoot
					/*
                    {
                      "access_token": "the_access_token",
                      "token_type": "bearer",
                      "refresh_token": "the_refresh_token",
                      "expires_in": 59,
                      "scope": "the space separated list of scopes",
                      "username": "username_of_the_user",
                      "jti": "a338c2f9-4bb0-4912-8a3e-faff4309e28b"
                      }
                      */

					let returnData = null;
					response.setEncoding("utf8");

					response.on("data", (d) => {
						if (returnData === null) {
							returnData = Buffer.from(d);
						} else {
							returnData += d;
						}
					});

					// Would need some error handling
					// request.on("error", …)

					response.on("error", (e) => {
						res.setHeader("Content-Type", "text/plain");
						res.send({
							errorMsg: e,
						});
						res.status(400);
					});

					response.on("end", () => {
						// NOTE We generate a website with a success message for the user and embed a JS that triggers the `postMessage` interface to communicate with the outer WebView of the mobile app
						res.setHeader("Content-Type", "text/html");
						res.send(`<!DOCTYPE html>
<html>
	<head>
		<meta charset="utf-8">
		<title>Komoot API authorized</title>

		<script type="text/javascript">

		//if(window.ReactNativeWebView) {
			console.log("Posting Message", '${returnData}');
			window.ReactNativeWebView.postMessage('${returnData}');
		//} else {
			// Show a message that this URL should only be opened from inside the FazuaApp
		//}
		</script>

	</head>

	<body>
		<h1>Thanks for authorizing the Komoot API</h1>

	</body>
</html>
                        	`);
					});
				}
			);

			request.on("error", (error) => {
				console.error(error);
			});

			request.end();
		});
	});

exports.connect = functions
	.region("europe-west3")
	.https.onRequest((req, res) => {
		cors(req, res, () => {
			res.status(200).send(`<!DOCTYPE html>
    <head>
      <title>Connect to Komoot</title>
    </head>
    <body>
      <a href="${komootAuthUrl}?client_id=${komootClientId}&response_type=code&redirect_uri=${encodeURIComponent(
				oAuthSuccessUrl
			)}&scope=profile">Connect to Komoot</button>
    </body>
  </html>`);
		});
	});
