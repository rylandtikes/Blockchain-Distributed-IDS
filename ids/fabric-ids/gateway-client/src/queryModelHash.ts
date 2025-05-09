import * as grpc from '@grpc/grpc-js';
import { connect, Identity, Signer, signers } from '@hyperledger/fabric-gateway';
import * as crypto from 'crypto';
import { promises as fs } from 'fs';
import * as path from 'path';

const channelName = 'mychannel';
const chaincodeName = 'model';
const mspId = 'Org1MSP';

const cryptoPath = path.resolve(__dirname, '..', '..', '..', 'fabric-ids', 'fabric-ids-network', 'organizations', 'peerOrganizations', 'org1.example.com');
const keyDirectoryPath = path.resolve(cryptoPath, 'users', 'User1@org1.example.com', 'msp', 'keystore');
const certDirectoryPath = path.resolve(cryptoPath, 'users', 'User1@org1.example.com', 'msp', 'signcerts');
const tlsCertPath = path.resolve(cryptoPath, 'peers', 'peer0.org1.example.com', 'tls', 'ca.crt');
const peerEndpoint = '192.168.0.59:7051'; // node-beta
const peerHostAlias = 'peer0.org1.example.com';

async function main(): Promise<void> {
    const assetId = process.argv[2];
    if (!assetId) {
        console.error('Usage: node dist/queryModelHash.js <MODEL_HASH>');
        process.exit(1);
    }

    const client = await newGrpcConnection();
    const gateway = connect({
        client,
        identity: await newIdentity(),
        signer: await newSigner(),
    });

    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);

        console.log(`Querying model hash: ${assetId}`);
        const resultBytes = await contract.evaluateTransaction('ReadModelUpdate', assetId);
	const resultJson = Buffer.from(resultBytes).toString('utf8');
        console.log('✔️  Query result:\n', JSON.parse(resultJson));
    } catch (error: any) {
        console.error('✖️  Query failed:', error.message || error);
    } finally {
        gateway.close();
        client.close();
    }
}

async function newGrpcConnection(): Promise<grpc.Client> {
    const tlsRootCert = await fs.readFile(tlsCertPath);
    const tlsCredentials = grpc.credentials.createSsl(tlsRootCert);
    return new grpc.Client(peerEndpoint, tlsCredentials, {
        'grpc.ssl_target_name_override': peerHostAlias,
    });
}

async function newIdentity(): Promise<Identity> {
    const certFile = (await fs.readdir(certDirectoryPath)).find(f => f.endsWith('.pem'));
    if (!certFile) throw new Error('Certificate file not found');
    const credentials = await fs.readFile(path.join(certDirectoryPath, certFile));
    return { mspId, credentials };
}

async function newSigner(): Promise<Signer> {
    const keyFile = (await fs.readdir(keyDirectoryPath))[0];
    if (!keyFile) throw new Error('Private key file not found');
    const privateKeyPem = await fs.readFile(path.join(keyDirectoryPath, keyFile));
    const privateKey = crypto.createPrivateKey(privateKeyPem);
    return signers.newPrivateKeySigner(privateKey);
}

main();

