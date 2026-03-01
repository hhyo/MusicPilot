"""
TransferChain 简单测试
"""

import pytest


class TestTransferChainSimple:
    """TransferChain 简单测试"""

    @pytest.mark.asyncio
    async def test_transfer_chain_imports(self):
        """测试 TransferChain 可导入"""
        from app.chain.transfer import TransferChain
        assert TransferChain is not None

    def test_transfer_chain_module(self):
        """测试 transfer chain 模块"""
        from app.chain import transfer
        assert transfer is not None
