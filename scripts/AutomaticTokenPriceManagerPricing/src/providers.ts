import { ethers } from "ethers";

const alchemyKey = process.env.ATPMP_ALCHEMY_KEY || process.exit(1);
const walletKey = process.env.ATPMP_PRIVATE_KEY || process.exit(1);

export const alchemyProvider = new ethers.providers.AlchemyProvider("matic", alchemyKey);
export const ethersWallet = new ethers.Wallet(walletKey, alchemyProvider);