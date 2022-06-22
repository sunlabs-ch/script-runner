import { FixedNumber, BigNumber, Contract } from "ethers";
import { tokenSet0x } from "./pricing";
import { priceSet } from "./management";

interface Address {
	symbol: string;
	decimals: number;
	pricing: (decimals: number, arg2: Contract) => Promise<FixedNumber>;
	management: (manager: Contract, price: BigNumber) => Promise<boolean>;
	lastPrice: BigNumber;
}

export const ZERO = BigNumber.from(0);

export const ADDRESSES: Address[] = [
	{
		symbol: "QME",
		decimals: 18,
		pricing: tokenSet0x,
		management: priceSet,
		lastPrice: ZERO
	}
];