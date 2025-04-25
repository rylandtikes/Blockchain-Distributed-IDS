import * as grpc from '@grpc/grpc-js';
import { connect, Identity, Signer, signers } from '@hyperledger/fabric-gateway';
import * as crypto from 'crypto';
import { promises as fs } from 'fs';
import * as path from 'path';

const channelName = 'mychannel';
const chaincodeName = 'basic';
const mspId = 'Org1MSP';

const cryptoPath = path.resolve(__dirname, '..', '..', '..', 'test-network', 'organizations', 'peerOrganizations', 'org1.example.com');
const keyDirectoryPath = path.resolve(cryptoPath, 'users', 'User1@org1.example.com', 'msp', 'keystore');
const certDirectoryPath = path.resolve(cryptoPath, 'users', 'User1@org1.example.com', 'msp', 'signcerts');
const tlsCertPath = path.resolve(cryptoPath, 'peers', 'peer0.org1.example.com', 'tls', 'ca.crt');
const peerEndpoint = 'localhost:7051';
const peerHostAlias = 'peer0.org1.example.com';

async function main(): Promise<void> {
    const client = await newGrpcConnection();

    const gateway = connect({
        client,
        identity: await newIdentity(),
        signer: await newSigner(),
        evaluateOptions: () => ({ deadline: Date.now() + 5000 }),
        endorseOptions: () => ({ deadline: Date.now() + 15000 }),
        submitOptions: () => ({ deadline: Date.now() + 5000 }),
        commitStatusOptions: () => ({ deadline: Date.now() + 60000 }),
    });

    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);

        const logPath = path.resolve('/home/rtikes/ml-data/flower/model_hashes.log');
        const logContent = await fs.readFile(logPath, 'utf8');
        const lastLine = logContent.trim().split('\n').pop();

        if (!lastLine) throw new Error('No entries found in model_hashes.log');

        const [nodeId, timestamp, modelHash] = lastLine.split(',');

        if (!nodeId || !timestamp || !modelHash) {
            throw new Error(`Invalid log format: "${lastLine}"`);
        }

        const assetId = modelHash;

        console.log('Submitting CreateAsset transaction...');
        await contract.submitTransaction('CreateAsset', assetId, timestamp, '1', nodeId, '0');
        console.log('CreateAsset transaction submitted.');

        console.log('Querying asset to verify...');
        const resultBytes = await contract.evaluateTransaction('ReadAsset', assetId);
        const resultJson = Buffer.from(resultBytes).toString('utf8');
        console.log('Query result:', JSON.parse(resultJson));

    } catch (error) {
        console.error('Error:', error);
        process.exitCode = 1;
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
    const files = await fs.readdir(certDirectoryPath);
    const certFile = files.find(f => f.endsWith('.pem'));
    if (!certFile) throw new Error('Certificate file not found');
    const certPath = path.join(certDirectoryPath, certFile);
    const credentials = await fs.readFile(certPath);
    return { mspId, credentials };
}

async function newSigner(): Promise<Signer> {
    const files = await fs.readdir(keyDirectoryPath);
    const keyFile = files[0];
    if (!keyFile) throw new Error('Private key file not found');
    const keyPath = path.join(keyDirectoryPath, keyFile);
    const privateKeyPem = await fs.readFile(keyPath);
    const privateKey = crypto.createPrivateKey(privateKeyPem);
    return signers.newPrivateKeySigner(privateKey);
}

main();
