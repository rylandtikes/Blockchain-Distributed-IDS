import {Object, Property} from 'fabric-contract-api';

@Object()
export class ModelUpdate {
    @Property()
    public hash: string = '';

    @Property()
    public timestamp: string = '';

    @Property()
    public node_id: string = '';
}

