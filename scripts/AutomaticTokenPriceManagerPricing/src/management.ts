import axios, { AxiosResponse } from "axios";
import { BigNumber, Contract, ethers, utils } from "ethers";
import { ethersWallet } from "./providers";
import { automatedAdmin } from "./abi";

const printErrors: boolean = process.env.ATPMP_TX_ERRORS?.toLowerCase() === "true" || false;

interface GasFees {
	maxPriorityFee: number;
	maxFee: number;
}

interface GasStation {
	safeLow: GasFees;
	standard: GasFees;
	fast: GasFees;
	estimatedBaseFee: number;
	blockTime: number;
	blockNumber: number;
}

export const priceSet = async (manager: Contract, price: BigNumber) => {
	const admin = automatedAdmin.connect(ethersWallet);
	const data = utils.hexConcat(["0x91b7f5ed", utils.hexZeroPad(price._hex, 32)]);
	const fees = await axios({
		method: 'get',
		url: 'https://gasstation-mainnet.matic.network/v2'
	}).then((res) => { return res.data as GasStation });
	const overrides = {
		gasLimit: 100000,
		maxFeePerGas: ethers.utils.parseUnits(
			Math.ceil(fees.fast.maxFee) + '',
			'gwei'
		),
		maxPriorityFeePerGas: ethers.utils.parseUnits(
			Math.ceil(fees.fast.maxPriorityFee) + '',
			'gwei'
		)
	};
	try {
		const tx = await admin.contractCall(manager.address, data, overrides);
		return (await tx.wait()).status !== 0;
	}
	catch (e) {
		if (printErrors) { console.log(e); }
		return false;
	}
}