#!/usr/bin/env node

import { BigNumber } from "ethers";
import { ToadScheduler, SimpleIntervalJob, AsyncTask } from "toad-scheduler";
import { ADDRESSES, ZERO } from "./addresses";
import { tokenPriceController, tokenPriceManager, setToken } from "./abi";

process.on('unhandledRejection', (err, origin) => {
	console.log("[" + dayjs().format() + "]: Unhandled rejection.");
	console.log(err);
	console.log(origin);
});

const dayjs = require('dayjs');

const publicAddress = process.env.ATPMP_PUBLIC_ADDRESS || process.exit(1);

const promiseWithTimeout = <T>(timeoutMs: number, promise: Promise<T>, failureMessage?: string) => {
	let timeoutHandle: NodeJS.Timeout;
	const timeoutPromise = new Promise<never>((resolve, reject) => {
		timeoutHandle = setTimeout(() => reject(new Error(failureMessage)), timeoutMs);
	});

	return Promise.race([
		promise,
		timeoutPromise,
	]).then((result) => {
		clearTimeout(timeoutHandle);
		return result;
	});
}

const main = async () => {
	ADDRESSES.forEach(async (a) => {
		const manager = tokenPriceManager.attach(await tokenPriceController.getManager(a.symbol));
		const primary = setToken.attach(await manager.getTokenPrimary());
		if (a.lastPrice.eq(ZERO)) {
			a.lastPrice = await manager.price();
		}
		const feeSpread: number = (await manager.slot0()).pricePercentFeeSpread;
		const priceLegible = await a.pricing(a.decimals, primary);
		const priceZerox = BigNumber.from(priceLegible._hex);
		const priceUpper = priceZerox.mul(1000 + feeSpread).div(1000);
		const priceLower = priceZerox.mul(1000 - feeSpread).div(1000);
		if (a.lastPrice.lt(priceLower) || a.lastPrice.gt(priceUpper)) {
			const success = promiseWithTimeout<boolean>(
				180000,
				a.management(manager, priceZerox),
				"[" + dayjs().format() + " " + a.symbol + " " + publicAddress + "]: Price change timed out."
			)
				.catch((e) => {
					console.log(e);
					return new Promise<boolean>((resolve,) => resolve(false));
				});
			if (await success) {
				a.lastPrice = priceZerox;
				console.log(
					"[" + dayjs().format() + " " + a.symbol + " " + publicAddress + "]: Price changed to " + priceLegible.toString() +"."
				);
			} else {
				a.lastPrice = ZERO;
				console.log(
					"[" + dayjs().format() + " " + a.symbol + " " + publicAddress + "]: Price change failed."
				);
			}
		} else {
			console.log(
				"[" + dayjs().format() + " " + a.symbol + " TPMAutomation]: No changes."
			);
		}
	});
}

const scheduler = new ToadScheduler();
const task = new AsyncTask('Main loop', main);
const job = new SimpleIntervalJob({ minutes: 5, }, task);

scheduler.addSimpleIntervalJob(job);