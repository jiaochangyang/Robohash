// Setting up wallet
// Choose between Metamask or MyEtherWallet or something else
if (window.ethereum !== null) {
	window.web3 = new Web3(ethereum);
} else {
	window.web3 = new Web3();
  web3.setProvider(new web3.providers.HttpProvider('https://api.myetherwallet.com/rop'));
}

// Setting up the contract details
// Read the ABI from the HTML
const asynchromixABI = JSON.parse($("#robohash-abi").text());
const contractAddress = "0xC771a49494047e548F4DfFCCC39b5636FF4c81d8"; // "0x99b52b88cb552a7f8582edcb03984f5fb4360c92";
let contract = new web3.eth.Contract(asynchromixABI, contractAddress);
window.contract = contract;


// Functions for transforming the input into MPC's input
function extended_gcd(a, b) {
  var s = BigInt(0); var old_s = BigInt(1);
  var t = BigInt(1); var old_t = BigInt(0);
  var r = b; var old_r = a;

  while (r !== BigInt(0)) {
    quotient = ~~(old_r / r);
    [old_r, r] = [r, old_r - quotient * r];
    [old_s, s] = [s, old_s - quotient * s];
    [old_t, t] = [t, old_t - quotient * t];
  }

  return [old_r, old_s, old_t];
}
function mod_reduce(x, p) {
  var r = x % p;
  return r >= 0 ? r : r + p;
}
function modular_inverse(x, p) {
  var gcd, s, t;
  [gcd, s, t] = extended_gcd(x, p);
  return gcd > 0 ? s : -s;
}
function interpolate(n, t, r, p) {
  if (r.length !== n) {
    return false
  }
  var f0 = BigInt(0);
  var f;
  for (var i = 0; i <= t; i++) {
    f = BigInt(1);
    for (var j = 0; j <= t; j++) {
      if (i !== j) {
        f *= mod_reduce((BigInt(0) - BigInt(j + 1)) * modular_inverse(BigInt(i - j), p), p);
      }
    }
    f0 += mod_reduce(r[i] * f, p);
  }
  return mod_reduce(f0, p);
}
p = BigInt("52435875175126190479447740508185965837690552500527637822603658699938581184513");

// Setting up async promises handler
// Web3 uses the wrong convention, err handler first.
// As a result this snippet is necessary to use await
// https://ethereum.stackexchange.com/questions/54564/async-with-getaccounts
promisify = (fun, params=[]) => {
  return new Promise((resolve, reject) => {
    fun(...params, (err, data) => {
      if (err !== null) reject(err);
      else resolve(data);
    });
  });
}

// Functions to handle Ethereum interactions and events
function waitForReceipt(hash, cb) {
  web3.eth.getTransactionReceipt(hash, function (error, receipt) {
    if (error !== null || (receipt !== null && receipt.blockNumber !== null)) {
      // Transaction went through
      cb(error, receipt);
    } else {
      // Try again in 1 second
      window.setTimeout(function () {
        waitForReceipt(hash, cb);
      }, 1000);
    }
  });
}
function waitEvent(event, tr) {
  return new Promise( (resolve, reject) => {
   event(
    {},
    {fromBlock: tr.blockNumber, toBlock: tr.blockNumber})
   .get( function(error, logs) {
     for (var i = 0; i < logs.length; i++) {
         if (logs[i].transactionHash == tr.transactionHash) {
            resolve(logs[i]);
            return;
         }
         error();
     }
   });
  });
}
window.waitEvent = waitEvent;
async function deposit() {
// 100000000000000000     // 0.1 ETH
    let txhash = await promisify(contract.methods.deposit, [{from:web3.eth.defaultAccount, value:100000}]);
}
window.deposit = deposit;
async function go() {

	// We need to ask permission to view the user's account (for privacy mode)
  //await ethereum.enable(); // It will soon be deprecated
	const accounts = await ethereum.send('eth_requestAccounts');

  // Metamask features
  const version = await promisify(web3.eth.getNodeInfo);
  const network = await promisify(web3.eth.net.getNetworkType);
  $("#version").text(version + ' / ' + network);

  // Get the current metamask account (or allow to select others)
  try {
  	$("#default_account").text(await promisify(web3.eth.getAccounts));
  } catch (e) {
		$("#default_account").text(e);
  }

  // block number
  const block_number = await promisify(web3.eth.getBlockNumber);
  $("#block_number").text(block_number);
}
window.go = go;
go();
setInterval(go, 2000);


async function fetch_inputmasks(srv, idx) {
  url = "http://172.17.0.2:" + (8080+srv) + "/inputmask/" + idx + "/";
	let mask = await (await fetch(url)).json();
  return BigInt(mask.share);
}
window.fetch_inputmasks = fetch_inputmasks;

async function submit_input() {
	let mother_token = $("#mother_token").val();
	let father_token = $("#father_token").val();

	/*
	// Step 5: Publish the masked input (m + r) for breeding
	let txhash = await promisify(contract.methods.approveForBreeding, [mother_token, father_token, {from: web3.eth.defaultAccount}]);
	let tr = await promisify(waitForReceipt, [txhash]);
	let born_event = await waitEvent(contract.methods.childIsBorn);
	$("#child_token").text(born_event.args.idx.c[0]);
	$("#child_img").attr("src","dad.png");
	//*/
	let hash = web3.utils.keccak256(mother_token+":"+father_token);
	$("#child_token").val(hash);
	$("#child_img").attr("src","/img/"+mother_token+":"+father_token);

}
window.submit_input = submit_input;
$("#generate_child").click(submit_input);

async function request_genome_from_token(parent){
	// Requesting the user secret genome
	let parent_id = $("#"+parent+"_token").val();

	/*
	// Step 1: Claim an input mask
  let txhash = await promisify(contract.methods.reserve_inputmask, [{from: web3.eth.defaultAccount}]);
  console.log('Tx Hash!' + txhash);
  let tr = await promisify(waitForReceipt, [txhash]);

	let inputmask_event = await waitEvent(contract.methods.InputMaskClaimed, tr);
  let inputmask_idx = inputmask_event.args.inputmask_idx.c[0];
  console.log(inputmask_event);
  $("#inputmask_idx").text(inputmask_idx);

  // Step 2: Fetch the input mask from servers [r]
  let mask0 = await fetch_inputmasks(0, inputmask_idx);
  let mask1 = await fetch_inputmasks(1, inputmask_idx);
  let mask2 = await fetch_inputmasks(2, inputmask_idx);
  let mask3 = await fetch_inputmasks(3, inputmask_idx);

  // Step 3: Reconstruct the input mask r
  let rec = interpolate(4, 1, [mask0, mask1, mask2, mask3], p);
  $("#"+parent+"_genome").val(rec);
	$("#"+parent+"_img").attr("src","/"+rec);
	//*/
	$("#"+parent+"_img").attr("src","/img/"+parent_id+":"+parent_id);

}

$('#mother_token').on('keydown', function () {
  request_genome_from_token('mother');
});

$('#father_token').on('keydown', function () {
  request_genome_from_token('father');
});


$("#mother_private_genome_link").click(()=>{
	$('#modal').css({ display: "block" });
	$('#modal').addClass('show');
});
$("#father_private_genome_link").click(()=>{
	$('#modal').css({ display: "block" });
	$('#modal').addClass('show');
});
$("#child_private_genome_link").click(()=>{
	$('#modal').css({ display: "block" });
	$('#modal').addClass('show');
});
$("#close_modal").click(async ()=>{
	$('#modal').css({ display: "none" });
	$('#modal').removeClass('show');
});
