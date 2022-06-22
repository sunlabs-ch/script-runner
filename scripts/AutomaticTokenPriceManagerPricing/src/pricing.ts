import axios from "axios";
import { BigNumber, Contract, FixedNumber, utils } from "ethers";
import { FixedFormat } from "@ethersproject/bignumber";
import { erc20Token } from "./abi";

const { remove_outliers } = require("peirce-criterion");

const baseUrl0x = process.env.ATPMP_0X_URL || process.exit(1);
const decimalMap = new Map<string, number>();

interface Positions {
	component: string;
	module: string;
	unit: BigNumber;
	positionState: number;
	data: string;
}

interface ZeroxInput {
	symbol: string;
	decimals: number;
	tokenAddress: string;
}

interface ZeroxOutput {
	symbol: string;
	prices: number[];
}

export const tokenSet0x = async (decimals: number, setToken: Contract) => {
	const positions: Positions[] = await setToken.getPositions(); 
	const buyTokens: Promise<ZeroxInput>[] = positions.map(async (p, i) => {
		if (!decimalMap.has(p.component)) {
			decimalMap.set(p.component, await erc20Token.attach(p.component).decimals());
		}
		return {
			symbol: i.toString(),
			decimals: decimalMap.get(p.component) || 18,
			tokenAddress: p.component
		};
	});
	const jitter = Math.floor((Math.random() - 0.5) * 4);
	const output = await axios.post(baseUrl0x + `/history`, {
		buyTokens: await Promise.all(buyTokens),
		stepSize: 30 + jitter,
		stepCount: 4
	}).then((res) => { return res.data as ZeroxOutput[] })
	let totalValue = FixedNumber.from(0, "ufixed256x18");
	await Promise.all(
		output.map(async (o) => {
			let average = FixedNumber.from(0, "ufixed64x6");
			const trimmed = remove_outliers(o.prices) as number[];
			trimmed.forEach((n) =>
				average = average.addUnsafe(
					FixedNumber.from(n.toString(), "ufixed64x6")
				)
			);
			average = average.divUnsafe(FixedNumber.from(trimmed.length, "ufixed64x6"));
			const decimals = decimalMap.get(positions[+o.symbol].component) || 18;
			const positionFormat = FixedFormat.from({ signed: false, width: 256, decimals });
			totalValue = totalValue.addUnsafe(
				FixedNumber.fromBytes(
					positions[+o.symbol].unit._hex,
					positionFormat
				)
					.mulUnsafe(average.toFormat(positionFormat))
					.toFormat("ufixed256x18")
			)
		})
	);
	return totalValue;
}