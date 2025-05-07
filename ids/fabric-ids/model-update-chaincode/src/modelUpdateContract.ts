import {Context, Contract, Info, Returns, Transaction} from 'fabric-contract-api';
import {ModelUpdate} from './modelUpdate';
import stringify from 'json-stringify-deterministic';
import sortKeysRecursive from 'sort-keys-recursive';

@Info({title: 'ModelUpdate', description: 'Smart contract for model integrity logging'})
export class ModelUpdateContract extends Contract {

    @Transaction()
    public async CreateModelUpdate(ctx: Context, hash: string, timestamp: string, node_id: string): Promise<void> {
        const exists = await this.ModelUpdateExists(ctx, hash);
        if (exists) {
            throw new Error(`The model hash ${hash} already exists`);
        }

        const update: ModelUpdate = {
            hash,
            timestamp,
            node_id,
        };
        await ctx.stub.putState(hash, Buffer.from(stringify(sortKeysRecursive(update))));
    }

    @Transaction(false)
    @Returns('string')
    public async ReadModelUpdate(ctx: Context, hash: string): Promise<string> {
        const data = await ctx.stub.getState(hash);
        if (!data || data.length === 0) {
            throw new Error(`Model update ${hash} does not exist`);
        }
        return data.toString();
    }

    @Transaction(false)
    @Returns('boolean')
    public async ModelUpdateExists(ctx: Context, hash: string): Promise<boolean> {
        const data = await ctx.stub.getState(hash);
        return !!data && data.length > 0;
    }
}

