import * as grpc from '@grpc/grpc-js';
import { connect, Identity, Signer, signers } from '@hyperledger/fabric-gateway';
import * as crypto from 'crypto';
import { promises as fs } from 'fs';
import * as path from 'path';

const channelName = 'mychannel';
const chaincodeName = 'basic';

async function newGrpcConnection(): Promise<grpc.Client> {
    const tlsRootCert = await fs.readFile(path.resolve(__dirname, '..', '..', 'fabric-ids-network', 'organizations', 'peerOrganizations', 'org1.example.com', 'peers', 'peer0.org1.example.com', 'tls', 'ca.crt'));
    const tlsCredentials = grpc.credentials.createSsl(tlsRootCert);
    return new grpc.Client('localhost:7051', tlsCredentials, {
        'grpc.ssl_target_name_override': 'peer0.org1.example.com',
    });
}

async function newIdentity(): Promise<Identity> {
    const certPath = path.resolve(__dirname, '..', '..', 'fabric-ids-network', 'organizations', 'peerOrganizations', 'org1.example.com', 'users', 'User1@org1.example.com', 'msp', 'signcerts');
    const files = await fs.readdir(certPath);
    const certFile = files.find((f: string) => f.endsWith('.pem'));
    if (!certFile) throw new Error('No certificate found');
    const credentials = await fs.readFile(path.join(certPath, certFile));
    return { mspId: 'Org1MSP', credentials };
}

async function newSigner(): Promise<Signer> {
    const keyPath = path.resolve(__dirname, '..', '..', 'fabric-ids-network', 'organizations', 'peerOrganizations', 'org1.example.com', 'users', 'User1@org1.example.com', 'msp', 'keystore');
    const files = await fs.readdir(keyPath);
    const keyFile = files.find((f: string) => f.endsWith('_sk'));
    if (!keyFile) throw new Error('No private key found');
    const privateKeyPem = await fs.readFile(path.join(keyPath, keyFile));
    const privateKey = crypto.createPrivateKey(privateKeyPem);
    return signers.newPrivateKeySigner(privateKey);
}

async function runSybilTest(): Promise<void> {
    console.log('Starting enhanced Sybil resistance test...');
    
    const testId = Date.now();
    const results: any = {
        testDate: new Date().toISOString(),
        testId: testId,
        attacks: {
            typeA: { name: "Identity Multiplication", attempted: 0, blocked: 0 },
            typeB: { name: "Credential Cloning", attempted: 0, blocked: 0 },
            typeC: { name: "Collusion", attempted: 0, blocked: 0 }
        },
        performance: { enrollments: [], modelUpdates: [] },
        logs: []
    };

    const client = await newGrpcConnection();
    const gateway = connect({
        client,
        identity: await newIdentity(),
        signer: await newSigner(),
    });

    try {
        const network = gateway.getNetwork(channelName);
        const contract = network.getContract(chaincodeName);
        const timestamp = new Date().toISOString();

        // Test Type A: Identity Multiplication (Rate Limiting)
        console.log('Testing Type A: Identity Multiplication...');
        for (let i = 0; i < 8; i++) { 
            results.attacks.typeA.attempted++;
            const startTime = Date.now();
            try {
                await contract.submitTransaction('EnrollDevice', `rapid-${testId}-${i}`, crypto.randomBytes(8).toString('hex'), 'SENSOR', timestamp);
                console.log(`  Device ${i} enrolled successfully`);
            } catch (error: any) {
                results.attacks.typeA.blocked++;
                results.logs.push({ type: 'TypeA', message: error.message });
                console.log(`  Device ${i} blocked: ${error.message.includes('rate limit') ? 'Rate limited' : 'Other error'}`);
            }
            results.performance.enrollments.push(Date.now() - startTime);
        }

        // Test Type B: Credential Cloning
        console.log('Testing Type B: Credential Cloning...');
        const legitimateKey = crypto.randomBytes(16).toString('hex');
        
        try {
            await contract.submitTransaction('EnrollDevice', `legit-${testId}`, legitimateKey, 'SENSOR', timestamp);
            console.log('  Legitimate device enrolled');
        } catch (error: any) {
            console.log(`  Legitimate device enrollment failed: ${error.message}`);
        }
        
        for (let i = 0; i < 3; i++) {
            results.attacks.typeB.attempted++;
            try {
                await contract.submitTransaction('EnrollDevice', `clone-${testId}-${i}`, legitimateKey, 'SENSOR', timestamp);
                console.log(`  Clone ${i} enrolled - SECURITY ISSUE!`);
            } catch (error: any) {
                results.attacks.typeB.blocked++;
                results.logs.push({ type: 'TypeB', message: error.message });
                console.log(`  Clone ${i} blocked: ${error.message.includes('already in use') ? 'Key already used' : 'Other error'}`);
            }
        }

        // Test Type C: Collusion (Duplicate Model Submission)
        console.log('Testing Type C: Collusion...');
        const collusionHash = crypto.createHash('sha256').update(`coordinated-model-${testId}`).digest('hex');
        
        for (let i = 0; i < 2; i++) {
            results.attacks.typeC.attempted++;
            const startTime = Date.now();
            try {
                await contract.submitTransaction('CreateModelUpdate', collusionHash, timestamp, `legit-${testId}`);
                console.log(`  Model submission ${i} successful`);
            } catch (error: any) {
                results.attacks.typeC.blocked++;
                results.logs.push({ type: 'TypeC', message: error.message });
                console.log(`  Model submission ${i} blocked: ${error.message.includes('already exists') ? 'Duplicate hash' : 'Other error'}`);
            }
            results.performance.modelUpdates.push(Date.now() - startTime);
        }

        // Calculate results
        const totalAttempts = results.attacks.typeA.attempted + results.attacks.typeB.attempted + results.attacks.typeC.attempted;
        const totalBlocked = results.attacks.typeA.blocked + results.attacks.typeB.blocked + results.attacks.typeC.blocked;
        
        const finalResults = {
            ...results,
            summary: {
                totalAttacks: totalAttempts,
                totalBlocked: totalBlocked,
                preventionRate: totalBlocked / totalAttempts,
                avgEnrollmentTime: results.performance.enrollments.reduce((a: number, b: number) => a + b, 0) / results.performance.enrollments.length,
                avgModelUpdateTime: results.performance.modelUpdates.length > 0 ? 
                    results.performance.modelUpdates.reduce((a: number, b: number) => a + b, 0) / results.performance.modelUpdates.length : 0
            }
        };

        await fs.writeFile('sybil-results.json', JSON.stringify(finalResults, null, 2));
        
        console.log('\n=== RESULTS ===');
        console.log(`Type A (Rate Limiting): ${results.attacks.typeA.blocked}/${results.attacks.typeA.attempted} blocked (${(results.attacks.typeA.blocked/results.attacks.typeA.attempted*100).toFixed(1)}%)`);
        console.log(`Type B (Credential Cloning): ${results.attacks.typeB.blocked}/${results.attacks.typeB.attempted} blocked (${(results.attacks.typeB.blocked/results.attacks.typeB.attempted*100).toFixed(1)}%)`);
        console.log(`Type C (Collusion): ${results.attacks.typeC.blocked}/${results.attacks.typeC.attempted} blocked (${(results.attacks.typeC.blocked/results.attacks.typeC.attempted*100).toFixed(1)}%)`);
        console.log(`Overall Prevention Rate: ${(finalResults.summary.preventionRate * 100).toFixed(1)}%`);
        console.log('Results saved to sybil-results.json');

    } finally {
        gateway.close();
        client.close();
    }
}

if (require.main === module) {
    runSybilTest().catch(console.error);
}

